# Aula 11 — Deploy AWS: Fargate, Escalabilidade e HTTPS

## Objetivo

Evoluir do EC2 (servidor que você gerencia) para o Fargate (container sem servidor), entender a decisão de custo entre as duas abordagens, configurar HTTPS com um domínio real e comparar os cenários de uso de cada opção de deploy.

---

# 1. O Limite do EC2

O EC2 da aula anterior resolveu o problema de "colocar no ar". Mas ele tem uma característica importante: **você gerencia o servidor**.

Isso significa:
- Atualizações de segurança do OS são sua responsabilidade
- Se o servidor tiver pico de usuários, você precisa manualmente aumentar o tamanho da instância
- Se você quiser duas instâncias para alta disponibilidade, precisa configurar um Load Balancer manualmente
- O servidor paga por hora — mesmo quando ninguém está usando

Para um projeto de portfólio, isso é aceitável. Para um produto real com usuários ativos, existe uma alternativa melhor: **ECS com Fargate**.

---

# 2. O que é ECS + Fargate

**ECS (Elastic Container Service)** é o serviço de orquestração de containers da AWS. Você descreve o que quer rodar (qual container, quanta CPU, quanta memória) e o ECS garante que esteja rodando.

**Fargate** é o modo de execução onde a AWS gerencia o servidor por baixo — você não vê, não acessa, não mantém. Paga apenas pelos recursos que o container usa, por segundo.

```
EC2                              Fargate
┌─────────────────────┐         ┌─────────────────────┐
│  Servidor EC2        │         │  AWS gerencia        │
│  └─ OS (você cuida) │         │  └─ OS invisível     │
│  └─ Docker          │         │  └─ Docker invisível │
│  └─ Seu container   │         │  └─ Seu container    │
└─────────────────────┘         └─────────────────────┘
Você paga: hora do servidor      Você paga: vCPU+RAM por segundo
```

---

# 3. Publicando a Imagem no ECR

O ECR (Elastic Container Registry) é o repositório de imagens da AWS — equivalente ao Docker Hub, mas privado e integrado ao ECS.

```bash
# Na sua máquina local

# 1. Autenticar com a AWS
aws configure  # insira suas credenciais (access key + secret)

# 2. Login no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  SEU-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Criar o repositório no ECR
aws ecr create-repository --repository-name sprint-fiap-backend --region us-east-1
aws ecr create-repository --repository-name sprint-fiap-frontend --region us-east-1

# 4. Build e push da imagem
docker build -t sprint-fiap-backend ./backend
docker tag sprint-fiap-backend:latest SEU-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/sprint-fiap-backend:latest
docker push SEU-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/sprint-fiap-backend:latest
```

---

# 4. Criando o Cluster e os Serviços ECS

**Via console AWS — ECS:**

```
1. ECS → Clusters → Create Cluster
   └─ Nome: sprint-fiap-cluster
   └─ Infra: AWS Fargate

2. Task Definitions → Create
   └─ Nome: sprint-backend-task
   └─ Launch type: Fargate
   └─ CPU: 0.5 vCPU, Memory: 1 GB  ← mínimo para o FastAPI
   └─ Container:
        Image URI: SEU-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/sprint-fiap-backend:latest
        Port: 8000
        Environment variables: (as mesmas do .env)

3. Services → Create
   └─ Task definition: sprint-backend-task
   └─ Service name: sprint-backend-service
   └─ Desired tasks: 1  ← quantas instâncias do container
   └─ Load balancer: Application Load Balancer (opcional)
```

---

# 5. Application Load Balancer — Distribuindo o Tráfego

O Load Balancer (ALB) distribui requisições entre múltiplas instâncias do container. Ele é também o ponto de entrada para HTTPS.

```
Internet
  │
  ▼
Application Load Balancer (porta 443, HTTPS)
  │
  ├─▶ sprint-backend container 1 (porta 8000)
  ├─▶ sprint-backend container 2 (porta 8000)  ← segundo container se escalar
  └─▶ sprint-frontend container 1 (porta 8501)
```

```
AWS Console → EC2 → Load Balancers → Create Load Balancer
  └─ Application Load Balancer
  └─ Scheme: Internet-facing
  └─ Listeners: HTTP:80, HTTPS:443
  └─ Target groups: um para o backend (:8000), um para o frontend (:8501)
```

---

# 6. HTTPS — Certificado SSL com AWS Certificate Manager

Nenhuma aplicação em produção deve rodar sem HTTPS. O AWS Certificate Manager (ACM) oferece certificados SSL gratuitos para domínios que você gerencia.

**Pré-requisitos:** você precisa de um domínio registrado (pode ser um domínio barato no Route 53 ou no Registro.br).

```bash
# 1. No ACM: Request certificate
AWS Console → Certificate Manager → Request
  └─ Domain: meuapp.com e *.meuapp.com (wildcard para subdomínios)
  └─ Validation: DNS validation (mais simples)

# 2. O ACM vai pedir que você adicione um registro CNAME no DNS do seu domínio
# Copie o CNAME fornecido e adicione na sua registradora de domínio

# 3. Após validação (pode levar até 30 min), o certificado fica com status "Issued"

# 4. No Load Balancer, adicione o listener HTTPS:443 com esse certificado
```

Com o certificado no ALB, o tráfego de `https://meuapp.com` termina no ALB com HTTPS e é encaminhado aos containers via HTTP interno — que é seguro porque está dentro da VPC (rede privada da AWS).

---

# 7. Auto Scaling — Escalando Quando Precisar

Com o Fargate, adicionar instâncias quando o tráfego aumenta é automático:

```
ECS → seu serviço → Update → Service auto scaling

Scaling policy:
  └─ Target tracking
  └─ Métrica: CPU utilization
  └─ Target: 70%  ← se a CPU média passar de 70%, adiciona containers
  └─ Min: 1 container
  └─ Max: 5 containers
```

Quando o tráfego cai, o Fargate remove os containers extras — e você para de pagar por eles.

---

# 8. Comparativo de Custo — EC2 vs Fargate

Para o projeto do Sprint (back + front):

```
EC2 t3.small (2 vCPU, 2 GB RAM) rodando 24/7:
  └─ ~$15/mês

Fargate (0.5 vCPU + 1 GB RAM por container, 2 containers):
  └─ 0.5 vCPU × $0.04048/hora × 720h = ~$14.57/mês
  └─ 1 GB × $0.004445/hora × 720h = ~$3.20/mês
  └─ Total: ~$18/mês

Fargate com 1 container (front e back juntos):
  └─ 0.5 vCPU + 1 GB = ~$8/mês
```

**Quando o Fargate é mais barato:**
- Carga variável — você não paga pelo servidor ocioso durante a madrugada
- Múltiplos ambientes (dev, staging, prod) que nem sempre estão todos ativos

**Quando o EC2 é mais barato:**
- Carga constante 24/7 — o servidor dedicado fica mais barato do que vCPU por segundo
- Instâncias reservadas (1 ou 3 anos) chegam a ter 70% de desconto sobre o preço sob demanda

---

# 9. Tabela de Decisão — Qual Deploy Usar

| Situação | Recomendação |
|---|---|
| Portfólio, demo, projeto acadêmico | Streamlit Cloud ou HF Spaces (gratuito) |
| App com API separada, portfólio avançado | EC2 t3.micro (free tier por 12 meses) |
| App em produção, time pequeno | Fargate + ALB |
| App com picos irregulares de uso | Fargate com auto scaling |
| API com execução rápida (< 15 min) e uso esporádico | Lambda |
| Startup com modelo pesado (GPU) | EC2 com instância g4dn (GPU) ou SageMaker |

---

# 10. O que Você Tem ao Final das Aulas 10 e 11

Você passou por três níveis de deploy:

```
Nível 1 — Plataformas gerenciadas (Aula 9)
  └─ Zero config, hibernate, sem controle
  └─ Streamlit Cloud, HF Spaces

Nível 2 — Servidor dedicado (Aula 10)
  └─ Controle total, mais responsabilidade
  └─ EC2 com Docker + docker-compose

Nível 3 — Container como serviço (Aula 11)
  └─ Sem servidor, escalável, HTTPS
  └─ ECS + Fargate + ALB + ACM
```

Um desenvolvedor que entende esses três níveis e sabe escolher entre eles dependendo do contexto está pronto para qualquer conversa técnica sobre infraestrutura de front-end de IA.

---

# Referências

- [AWS ECS + Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [AWS ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [AWS Certificate Manager](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html)
- [AWS Pricing Calculator](https://calculator.aws/pricing/2/home)
- [Fargate vs EC2 — AWS Blog](https://aws.amazon.com/blogs/containers/theoretical-cost-optimization-by-amazon-ecs-launch-type-fargate-vs-ec2/)
