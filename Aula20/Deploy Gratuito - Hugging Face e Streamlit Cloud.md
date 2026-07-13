# Aula 9 — Deploy Gratuito: Hugging Face Spaces e Streamlit Cloud

## Objetivo

Colocar o projeto no ar em plataformas gratuitas — sem servidor, sem configuração de infraestrutura. Entender as limitações de cada opção, quando usar cada uma, e como preparar o repositório para deploy automático.

---

# 1. Do docker-compose para o Ar

Na aula anterior containerizamos o projeto. Agora vamos usar esses containers (ou versões simplificadas) para fazer deploy público — acessível por qualquer pessoa com um link.

Três opções gratuitas:

| Plataforma | Melhor para | Limitações |
|---|---|---|
| Streamlit Community Cloud | Apps Streamlit puros (sem back-end separado) | Apenas Streamlit, sem FastAPI, sem Docker |
| Hugging Face Spaces | Gradio ou Streamlit com Docker | Sem GPU gratuita na versão básica, hiberna após inatividade |
| Hugging Face Spaces (Docker) | Qualquer app containerizado | Mesmo hibernamento, CPU limitada |

---

# 2. Streamlit Community Cloud

A opção mais rápida para projetos Streamlit. Deploy direto do repositório GitHub — sem Dockerfile.

**Pré-requisitos:**
- Conta no Streamlit Cloud (gratuita)
- Repositório público no GitHub com `app.py` na raiz ou em um caminho especificado
- `requirements.txt` com as dependências

**Passo a passo:**

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte sua conta GitHub
3. Selecione o repositório, branch e arquivo principal (`app.py`)
4. Configure os secrets (as variáveis que estavam em `.streamlit/secrets.toml`)
5. Clique em Deploy

```
# Estrutura mínima do repositório para Streamlit Cloud
meu-projeto/
├── app.py              ← arquivo principal
├── requirements.txt    ← dependências
└── .streamlit/
    └── config.toml     ← configurações opcionais (tema, etc.)
```

```toml
# .streamlit/config.toml  (pode ser commitado — não tem segredos)
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#31333F"
font = "sans serif"
```

Os secrets são configurados no painel do Streamlit Cloud — nunca no repositório:

```
Settings → Secrets →

API_URL = "https://meu-backend.onrender.com"
API_KEY = "chave-producao"
ANTHROPIC_API_KEY = "sk-ant-..."
```

**Limitação principal:** o Streamlit Cloud não roda FastAPI. Se o seu app precisa de um back-end separado, você precisa hospedar o FastAPI em outra plataforma (Render, Railway, ou cloud) e apontar `API_URL` para lá.

---

# 3. Hugging Face Spaces — Gradio

O Hugging Face Spaces é a forma mais natural de publicar um app Gradio. Ele detecta automaticamente o framework e faz o deploy.

```
# Estrutura mínima para Gradio no HF Spaces
meu-space/
├── app.py              ← o app Gradio
├── requirements.txt
└── README.md           ← com o bloco de metadados (obrigatório)
```

```markdown
---
title: Análise de Notícias
emoji: 📰
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: false
---

# Análise de Notícias com IA

Analisador de sentimento e resumo de notícias usando Claude.
```

O bloco `---` no topo do README é lido pelo Hugging Face para configurar o Space. Sem ele, o deploy pode falhar.

**Deploy via git:**

```bash
# O HF Spaces é um repositório Git
git clone https://huggingface.co/spaces/seu-usuario/meu-space
# Cole seus arquivos
git add .
git commit -m "deploy inicial"
git push
```

O deploy é automático a cada push — como o Streamlit Cloud.

**Configurando segredos no HF Spaces:**

No painel do Space: Settings → Repository secrets

```
ANTHROPIC_API_KEY = sk-ant-...
LANGCHAIN_API_KEY = ls__...
```

No código:

```python
import os
import gradio as gr

# os.environ lê as variáveis de ambiente — mesma forma que no servidor local
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
```

---

# 4. Hugging Face Spaces com Docker

Para projetos que têm front e back separados, o HF Spaces suporta Docker. Aqui você faz o deploy do container que criamos na Aula 08.

```markdown
---
title: Sprint FIAP
emoji: 🤖
colorFrom: purple
colorTo: pink
sdk: docker
pinned: false
---
```

```dockerfile
# Dockerfile (na raiz do Space)
# Neste caso rodamos front e back num único container para caber no tier gratuito
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Script de inicialização — sobe FastAPI em background e Streamlit em foreground
CMD ["sh", "-c", "uvicorn backend.main:app --port 8000 & streamlit run frontend/app.py --server.port=7860 --server.address=0.0.0.0"]
```

**Limitação importante:** no tier gratuito do HF Spaces, você tem apenas um container. Para rodar front e back no mesmo container (como acima), o FastAPI fica em background e o Streamlit fica em foreground. Funciona para demos e portfólio, mas não é a arquitetura de produção.

---

# 5. Quando Usar Cada Opção

```
Seu projeto é Streamlit puro (sem FastAPI)?
  └─ Streamlit Community Cloud — mais simples, deploy em 5 minutos

Seu projeto é Gradio?
  └─ Hugging Face Spaces (sdk: gradio) — a casa natural do Gradio

Seu projeto tem FastAPI + Streamlit/Gradio?
  └─ HF Spaces com Docker (tier gratuito, tudo junto)
     OU
  └─ FastAPI no Render/Railway (gratuito) + Streamlit Cloud para o front

Seu projeto precisa de GPU?
  └─ HF Spaces Pro (pago) ou AWS/GCP
```

---

# 6. Preparando o Repositório para Deploy

Checklist antes de qualquer deploy público:

```bash
# 1. Verificar que nenhum segredo está no código
grep -r "sk-ant" .           # chaves Anthropic
grep -r "API_KEY\s*=" .      # variáveis hardcoded
grep -r "password" .          # senhas
grep -r "localhost" .         # URLs locais que não funcionam em produção
```

```python
# Errado — hardcoded
ANTHROPIC_API_KEY = "sk-ant-abc123"

# Correto — variável de ambiente
import os
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY não configurada.")
```

```text
# .gitignore mínimo para projetos de IA
.env
*.env
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
venv/
*.log
```

---

# 7. Monitorando o Deploy

Após o deploy, tanto o Streamlit Cloud quanto o HF Spaces oferecem logs em tempo real:

```
# Streamlit Cloud
Manage app → Logs

# HF Spaces
Settings → Logs
```

Os erros mais comuns pós-deploy:

| Erro | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError` | Dependência não está no requirements.txt | Adicionar e fazer push |
| `KeyError` ou `None` em variável de ambiente | Secret não configurado na plataforma | Configurar no painel da plataforma |
| App hiberna | HF Spaces gratuito para após inatividade | Normal — acorda no próximo acesso |
| `ConnectionRefused` para a API | URL aponta para localhost | Trocar para URL de produção do back-end |

---

# 8. O que Você Tem ao Final desta Aula

- URL pública do seu projeto funcionando
- Secrets configurados na plataforma (não no código)
- `.gitignore` correto
- `requirements.txt` limpo e testado
- Um link que você pode colocar no LinkedIn, GitHub e currículo

Na próxima aula vamos dar o próximo passo: deploy em AWS, com controle real sobre infraestrutura, custo e escalabilidade.

---

# Referências

- [Streamlit Community Cloud](https://streamlit.io/cloud)
- [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces)
- [Hugging Face Spaces — Docker](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Render — Deploy FastAPI grátis](https://render.com)
- [Railway — Alternativa ao Render](https://railway.app)
