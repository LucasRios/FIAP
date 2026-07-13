# Aula 8 — Docker: Containerizando o App de IA

## Objetivo

Entender por que Docker é um conhecimento essencial para o desenvolvedor de front-end de IA, criar Dockerfiles para o Streamlit e para o FastAPI, e orquestrar os dois serviços com docker-compose — eliminando o "funciona na minha máquina" antes do deploy.

---

# 1. Por que Docker é Assunto de Front-end

A pergunta vai aparecer: "Docker não é coisa de DevOps?"

Pense no seguinte: você passa 3 semanas construindo seu projeto. Chega na hora de entregar — na máquina do avaliador, o Python é 3.9 em vez de 3.11. A versão do Streamlit é diferente. O `requirements.txt` tem um conflito de dependência. O app não sobe.

Docker resolve isso: você embala o app com tudo que ele precisa — Python, dependências, variáveis de ambiente — numa unidade chamada **container** que roda igual em qualquer máquina.

Para o desenvolvedor de front-end de IA especificamente:

**Portfolio:** projetos com Docker demonstram maturidade técnica. Um avaliador que clona seu repo e roda `docker-compose up` em vez de resolver dependências vai ter uma impressão muito melhor.

**Deploy:** todas as plataformas de cloud (Hugging Face Spaces com Docker, AWS ECS, Google Cloud Run) aceitam containers. Aprender Docker aqui é aprender a linguagem do deploy em nuvem.

**Colaboração:** se você trabalhar com um time de back-end, eles já usam Docker. Entender o básico elimina fricção.

---

# 2. Conceitos Fundamentais

```
Imagem (Image)
  └─ Um snapshot do sistema com tudo instalado
  └─ Como um molde — você define uma vez, usa várias vezes

Container
  └─ Uma instância rodando de uma imagem
  └─ Como um processo — pode ser iniciado, parado, destruído

Dockerfile
  └─ O receituário que define como criar a imagem
  └─ Sequência de instruções: qual OS, quais pacotes, quais arquivos

docker-compose
  └─ Orquestra múltiplos containers (front + back + banco)
  └─ Define como eles se comunicam entre si
```

---

# 3. Dockerfile para o FastAPI

```dockerfile
# backend/Dockerfile

# Ponto de partida: imagem oficial do Python 3.11 (versão slim = menor tamanho)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o requirements primeiro — aproveita o cache do Docker
# Se o requirements não mudou, essa camada não é reconstruída
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta que o FastAPI vai usar
EXPOSE 8000

# Comando que roda quando o container inicia
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```text
# backend/requirements.txt
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.7.0
httpx==0.27.0
python-dotenv==1.0.0
anthropic==0.40.0
langsmith==0.1.0
```

Construir e testar a imagem isoladamente:

```bash
cd backend
docker build -t sprint-backend .
docker run -p 8000:8000 --env-file .env sprint-backend
```

Acesse `http://localhost:8000/docs` — a API está rodando dentro do container.

---

# 4. Dockerfile para o Streamlit

```dockerfile
# frontend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do front-end
COPY . .

# Porta padrão do Streamlit
EXPOSE 8501

# Healthcheck: verifica se o app está respondendo a cada 30s
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# --server.address=0.0.0.0 permite acesso externo ao container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```text
# frontend/requirements.txt
streamlit==1.40.0
requests==2.32.0
python-dotenv==1.0.0
```

---

# 5. docker-compose — Orquestrando os Dois Serviços

Rodar front e back separadamente com dois terminais funciona em desenvolvimento, mas é frágil. O docker-compose define a relação entre os serviços em um único arquivo:

```yaml
# docker-compose.yml (na raiz do projeto)
version: "3.9"

services:

  backend:
    build: ./backend
    ports:
      - "8000:8000"          # host:container
    env_file:
      - ./backend/.env       # variáveis de ambiente do back
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    env_file:
      - ./frontend/.env
    environment:
      # O front se comunica com o back pelo nome do serviço — não por localhost
      - API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy  # espera o back estar saudável antes de subir
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

```bash
# Sobe tudo com um comando
docker-compose up --build

# Roda em segundo plano
docker-compose up --build -d

# Para tudo
docker-compose down

# Ver logs em tempo real
docker-compose logs -f
```

O detalhe crítico: dentro da rede Docker, os serviços se comunicam **pelo nome do serviço**, não por `localhost`. O front não chama `http://localhost:8000` — chama `http://backend:8000`. Por isso o `API_URL` no docker-compose usa `backend` como host.

---

# 6. Estrutura do Projeto com Docker

```
sprint-projeto/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── .env                  ← nunca commitar
│   ├── .env.example          ← commitar como template
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   └── providers/
├── frontend/
│   ├── Dockerfile
│   ├── .env                  ← nunca commitar
│   ├── .env.example          ← commitar como template
│   ├── requirements.txt
│   ├── app.py
│   └── features/
└── .gitignore
```

```text
# .gitignore
.env
*.env
__pycache__/
.streamlit/secrets.toml
```

```text
# backend/.env.example  ← este arquivo é commitado
API_KEY=sua-chave-aqui
ANTHROPIC_API_KEY=sua-chave-anthropic
LANGCHAIN_API_KEY=sua-chave-langsmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=sprint-fiap
```

---

# 7. Por que a Ordem das Instruções no Dockerfile Importa

O Docker usa cache em camadas. Cada instrução no Dockerfile é uma camada. Se uma camada muda, todas as posteriores são reconstruídas.

```dockerfile
# Ruim — qualquer mudança no código reinicia a instalação de dependências
COPY . .
RUN pip install -r requirements.txt

# Bom — dependências ficam em cache enquanto requirements.txt não mudar
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

Em prática: durante o desenvolvimento você muda o código com frequência e o requirements raramente. Com a ordem correta, o `pip install` roda apenas quando você adiciona uma nova dependência — não a cada mudança de código.

---

# 8. Verificando que Tudo Está Funcionando

```bash
# Sobe os serviços
docker-compose up --build

# Em outro terminal, verifica o status
docker-compose ps

# Saída esperada:
# NAME                STATUS          PORTS
# sprint-backend      Up (healthy)    0.0.0.0:8000->8000/tcp
# sprint-frontend     Up              0.0.0.0:8501->8501/tcp
```

Acesse:
- `http://localhost:8000/docs` — Swagger do back-end
- `http://localhost:8501` — App Streamlit

---

# Referências

- [Docker — Documentação Oficial](https://docs.docker.com)
- [Docker Compose](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Streamlit — Docker Deploy](https://docs.streamlit.io/deploy/tutorials/docker)
