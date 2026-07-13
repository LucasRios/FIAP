# Aula 10 — Deploy AWS: EC2 e Decisão de Arquitetura

## Objetivo

Entender as opções de deploy na AWS e quando usar cada uma, configurar uma instância EC2, rodar o projeto com docker-compose em produção e introduzir os conceitos de Security Groups e IAM que o desenvolvedor de front-end precisa conhecer.

---

# 1. Por que AWS e não Apenas Plataformas Gratuitas

As plataformas da Aula 9 (Streamlit Cloud, HF Spaces) são ótimas para portfólio e demos. Mas têm limitações reais:

- **Hibernam após inatividade:** o app fica offline automaticamente após minutos sem acesso
- **Recursos limitados:** CPU e RAM restritas, sem controle sobre o ambiente
- **Sem controle de rede:** você não configura firewall, não tem IP fixo, não controla quem acessa o quê
- **Sem persistência real:** nada além de bancos de dados externos, nenhuma escrita em disco persistente

O AWS resolve tudo isso — com custo e responsabilidade maiores. Saber escolher entre as opções é o que diferencia um desenvolvedor júnior de um sênior.

---

# 2. As Opções de Compute na AWS

```
Opções de onde rodar seu container / código na AWS:

EC2 (Virtual Machine)
  └─ Você aluga um servidor completo
  └─ Controle total: OS, rede, disco
  └─ Você gerencia tudo: atualizações, reinicialização, escalabilidade
  └─ Mais barato para carga constante

ECS + Fargate (Container sem servidor)
  └─ Você envia o container, a AWS gerencia o servidor
  └─ Paga por vCPU/memória por segundo (não pela hora do servidor)
  └─ Melhor para carga variável ou se você não quer gerenciar OS

Lambda (Serverless)
  └─ Código executado sob demanda, sem servidor visível
  └─ Excelente para APIs com picos de demanda irregulares
  └─ Limite de tempo de execução (15 min) — ruim para modelos lentos
  └─ Custo zero quando não está em uso

App Runner / Elastic Beanstalk
  └─ Abstrações de mais alto nível sobre EC2/ECS
  └─ Deploy simples de containers ou código
  └─ Menos controle, mais conveniência
```

Para o projeto da FIAP, **EC2 é a melhor escolha de aprendizado** — você vê tudo acontecendo, entende a infraestrutura, e o custo é controlável com uma instância pequena.

---

# 3. Criando a Instância EC2

**Via console AWS:**

1. Acesse [console.aws.amazon.com/ec2](https://console.aws.amazon.com/ec2)
2. "Launch Instance"
3. Configurações para o projeto:

```
Nome: sprint-fiap
AMI: Amazon Linux 2023  ← gratuita, boa compatibilidade com Docker
Instance type: t3.micro (free tier) ou t3.small para mais memória
Key pair: Crie um novo → baixe o .pem e guarde com segurança
Storage: 20 GB gp3 (suficiente para o projeto)
```

**Security Group** — o firewall da instância:

```
Inbound rules (o que pode entrar):
  SSH    | TCP | 22   | Seu IP (não 0.0.0.0/0)
  HTTP   | TCP | 80   | 0.0.0.0/0
  HTTPS  | TCP | 443  | 0.0.0.0/0
  Custom | TCP | 8000 | 0.0.0.0/0  ← FastAPI (apenas durante desenvolvimento)
  Custom | TCP | 8501 | 0.0.0.0/0  ← Streamlit (apenas durante desenvolvimento)

Outbound rules:
  All traffic | 0.0.0.0/0  ← permite saída para a internet (para chamar APIs externas)
```

**Nunca abra a porta 22 (SSH) para `0.0.0.0/0`** — qualquer pessoa na internet pode tentar acessar seu servidor. Restrinja ao seu IP.

---

# 4. Conectando e Configurando o Servidor

```bash
# Na sua máquina local — conectar via SSH
chmod 400 minha-chave.pem   # restringe permissões do arquivo (obrigatório no Linux/Mac)
ssh -i "minha-chave.pem" ec2-user@SEU-IP-PUBLICO
```

Após conectar, instalar o Docker:

```bash
# Atualizar o sistema
sudo dnf update -y

# Instalar Docker
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker       # inicia automaticamente com o servidor
sudo usermod -aG docker ec2-user  # permite rodar docker sem sudo

# Sair e reconectar para as permissões de grupo terem efeito
exit
ssh -i "minha-chave.pem" ec2-user@SEU-IP-PUBLICO

# Verificar instalação
docker --version

# Instalar docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

# 5. Copiando o Projeto para o Servidor

Duas opções:

**Opção A — Git clone (recomendada):**

```bash
# No servidor EC2
git clone https://github.com/seu-usuario/sprint-fiap.git
cd sprint-fiap

# Criar os arquivos .env que não foram commitados
nano backend/.env
nano frontend/.env
```

**Opção B — SCP (cópia direta):**

```bash
# Na sua máquina local
scp -i "minha-chave.pem" -r ./sprint-fiap ec2-user@SEU-IP:/home/ec2-user/
```

---

# 6. Subindo o Projeto

```bash
# No servidor EC2, dentro do diretório do projeto
docker-compose up --build -d

# Verificar que os containers estão rodando
docker-compose ps

# Acompanhar logs em tempo real
docker-compose logs -f

# Verificar uso de memória/CPU
docker stats
```

Teste acessando no browser:
- `http://SEU-IP:8000/docs` — Swagger do FastAPI
- `http://SEU-IP:8501` — Streamlit

---

# 7. IAM — O Sistema de Permissões da AWS

IAM (Identity and Access Management) controla **quem pode fazer o quê** na AWS. Para o desenvolvedor de front-end, o conhecimento mínimo necessário é sobre **IAM Roles para EC2**.

**Cenário:** seu app Streamlit/FastAPI precisa chamar o Amazon Bedrock (modelos de IA da AWS) ou ler arquivos do S3. Como ele se autentica?

**Opção ruim:** colocar a `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` no `.env`. Se o servidor for comprometido ou o arquivo vazar, suas credenciais estão expostas.

**Opção certa:** IAM Role para EC2

```
AWS Console → IAM → Roles → Create Role
  └─ Trusted entity: EC2
  └─ Permissions: adicionar apenas o que o app precisa
       AmazonBedrockFullAccess  (se usar Bedrock)
       AmazonS3ReadOnlyAccess   (se apenas lê do S3)
  └─ Nome: sprint-fiap-role

EC2 Console → sua instância → Actions → Security → Modify IAM Role
  └─ Selecionar sprint-fiap-role
```

Com a role associada, o SDK AWS no seu código encontra as credenciais automaticamente:

```python
import boto3

# Sem nenhuma credencial no código — a role do EC2 é usada automaticamente
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
```

**Princípio do menor privilégio:** dê apenas as permissões que o app realmente usa. Se ele só lê do S3, não dê permissão de escrita ou delete.

---

# 8. Mantendo o App Online

Por padrão, se o EC2 for reiniciado, os containers precisam ser reiniciados manualmente. Para fazer isso automático:

```bash
# Cria um serviço systemd que sobe os containers com o servidor
sudo nano /etc/systemd/system/sprint-fiap.service
```

```ini
[Unit]
Description=Sprint FIAP App
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/home/ec2-user/sprint-fiap
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
User=ec2-user

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sprint-fiap
sudo systemctl start sprint-fiap
```

---

# 9. Custo — O que Você Vai Pagar

```
Instância t3.micro (free tier por 12 meses):
  └─ $0.00 durante o free tier
  └─ ~$8/mês depois do free tier

Instância t3.small (além do free tier):
  └─ ~$15/mês

EBS Storage (20 GB gp3):
  └─ ~$1.60/mês

IP Elástico (IP fixo):
  └─ Gratuito enquanto associado à instância em uso
  └─ $0.005/hora se não estiver associado (então não aloque sem usar)

Transferência de dados de saída:
  └─ 100 GB/mês gratuitos, depois $0.09/GB
```

**Dica para o free tier:** a AWS oferece 750 horas/mês de t3.micro por 12 meses após criar a conta. Uma instância rodando 24/7 usa exatamente 730 horas/mês — cabe no free tier.

---

# Referências

- [AWS EC2 — Documentação](https://docs.aws.amazon.com/ec2/)
- [AWS IAM — Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Docker no Amazon Linux](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-container-image.html)
