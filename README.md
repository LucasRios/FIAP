# FIAP — Front-End em sistemas de IA

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-5.x-F97316?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20Fargate-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

Materiais, exercícios e projetos.

O curso cobre dois semestres: o primeiro constrói interfaces com Streamlit e Gradio; o segundo evolui o projeto para uma arquitetura separada com FastAPI, observabilidade com LangSmith, containerização com Docker, deploy na AWS e mobile via PWA.

---

## Semestre 1 — Interfaces e Arquitetura

### Aulas

| Aula | Tema | Tecnologias |
|---|---|---|
| [Aula 01](Aula01/) | Introdução ao Streamlit e o ecossistema de front-end para IA | Python, Streamlit |
| [Aula 02](Aula02/) | UX e Design System para IA | Streamlit, UX Principles |
| [Aula 03](Aula03/) | Input de dados, estado e callbacks | Streamlit Session State |
| [Aula 04](Aula04/) | Visualização de dados interativa | Plotly, Altair, Matplotlib, PyDeck |
| [Aula 05](Aula05/) | Caching, performance e conectividade com APIs | Streamlit Cache |
| [Aula 06](Aula06/) | Arquitetura modular — Feature-First e pipelines isolados | Features / Pipelines / Providers |
| [Aula 07](Aula07/) | Autenticação, RBAC e navegação por perfil | Streamlit Auth |
| [Aula 08](Aula08/) | Introdução ao Gradio — paradigma orientado a eventos | Python, Gradio |
| [Aula 09](Aula09/) | Gradio — UX, latência e streaming de tokens | Gradio, Streaming |
| [Aula 10](Aula10/) | Workshop de gráficos | Streamlit Charts |

### Checkpoints

**CheckPoint 1 — Generative AI Front-End**
Interface para modelo **Autoencoder Variacional (VAE)** de triagem de pneumonia.
- Stack: Python, Streamlit, TensorFlow/Keras
- Inclui modelo treinado (`vae_pneumonia.weights.h5`) e pipeline de inferência completo

**CheckPoint 2 — NLP Front-End**
Aplicação de análise de notícias com scraping e NLP.
- Stack: Python, Streamlit, NLP pipeline
- Arquitetura modular: features / pipelines / providers / state / ui

**Sprint de Referência**
Dashboard de gestão de equipamentos e sensores IoT.
- Stack: Python, Streamlit
- Módulos: cadastro, dashboard, equipamentos, sensores

### Arquitetura (Aulas 06+)

```
app.py
├── features/           ← páginas da aplicação por funcionalidade
│   └── nome_feature/
│       └── page.py
├── pipelines/          ← orquestração e lógica de negócio
├── providers/          ← acesso a dados, modelos e serviços externos
├── state/              ← gerenciamento de estado da sessão
└── ui/                 ← componentes visuais reutilizáveis
```

---

## Semestre 2 — Backend, Deploy e Mobile

### Aulas

| Aula | Tema | Tecnologias |
|---|---|---|
| [Aula 00](Semestre2/Aula00/) | Revisão do S1 e APIs para front-enders | HTTP, REST |
| [Aula 01](Semestre2/Aula01/) | FastAPI — do Python simples ao backend de IA | FastAPI, Pydantic, Uvicorn |
| [Aula 02](Semestre2/Aula02/) | Consumindo a API no front com Streamlit | Requests, API Key, st.secrets |
| [Aula 03](Semestre2/Aula03/) | Gradio, async, CORS e roteamento de modelos | HTTPX, CORS, versionamento |
| [Aula 04](Semestre2/Aula04/) | Workshop — refatorando o Sprint com FastAPI | FastAPI, python-dotenv |
| [Aula 05](Semestre2/Aula05/) | Observabilidade — a IA como caixa preta | LangSmith, logging estruturado |
| [Aula 06](Semestre2/Aula06/) | Observabilidade — instrumentando o pipeline | LangSmith, @traceable, feedback |
| [Aula 07](Semestre2/Aula07/) | LangChain no front-end | LangChain, Tools, Chain of Thought |
| [Aula 08](Semestre2/Aula08/) | Docker — containerizando o app de IA | Docker, docker-compose |
| [Aula 09](Semestre2/Aula09/) | Deploy gratuito — Hugging Face e Streamlit Cloud | HF Spaces, Streamlit Cloud |
| [Aula 10](Semestre2/Aula10/) | Deploy AWS — EC2 e decisão de arquitetura | EC2, IAM, Security Groups |
| [Aula 11](Semestre2/Aula11/) | Deploy AWS — Fargate, escalabilidade e HTTPS | ECS, Fargate, ALB, ACM |
| [Aula 12](Semestre2/Aula12/) | Mobile — PWA com o que você já tem | Web App Manifest, Service Worker |
| [Aula 13](Semestre2/Aula13/) | Mobile — além do PWA | Capacitor, Expo, TWA |
| [Aula 14](Semestre2/Aula14/) | Showcase — apresentação final | — |

### Arquitetura (Semestre 2)

```
┌─────────────────────┐     HTTP/REST     ┌─────────────────────────┐
│  Streamlit / Gradio │ ───────────────▶  │  FastAPI                │
│  (front-end)        │                   │  ├── routers/           │
│                     │                   │  ├── pipelines/         │
│  PWA / Capacitor    │                   │  └── providers/         │
│  (mobile)           │                   │       └── modelo de IA  │
└─────────────────────┘                   └─────────────────────────┘
           │                                          │
           │              LangSmith                   │
           └──────────── observabilidade ─────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Docker + docker-compose       │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  AWS EC2 / Fargate + HTTPS     │
               └───────────────────────────────┘
```

---

## Como Executar

**Semestre 1 — Streamlit / Gradio**

```bash
# Dentro de cada pasta de aula
pip install -r requirements.txt

streamlit run app.py   # para apps Streamlit
python app.py          # para apps Gradio
```

**Semestre 2 — FastAPI + Streamlit com Docker**

```bash
cd Semestre2

# Copie os arquivos de exemplo de variáveis de ambiente
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Preencha as chaves nos arquivos .env

# Suba front e back juntos
docker-compose up --build
```

Acesse:
- `http://localhost:8501` — front-end Streamlit
- `http://localhost:8000/docs` — documentação interativa da API (Swagger UI)

---

## Tecnologias

| Categoria | Tecnologias |
|---|---|
| **Interfaces** | Streamlit, Gradio |
| **Back-end** | FastAPI, Pydantic, Uvicorn |
| **HTTP / Async** | Requests, HTTPX |
| **IA / LLM** | Anthropic Claude, LangChain, LangSmith |
| **Visualização** | Plotly, Altair, Matplotlib, PyDeck |
| **Deploy** | Docker, docker-compose, AWS EC2, AWS Fargate, Hugging Face Spaces, Streamlit Cloud |
| **Mobile** | PWA (Web App Manifest + Service Worker), Capacitor |
| **Outros** | TensorFlow/Keras (CheckPoint 1), NLP pipeline (CheckPoint 2) |

---

## Instituição

**FIAP** — Faculdade de Informática e Administração Paulista  
Curso: Engenharia de Front-End para IA Generativa

---

## Licença

MIT
