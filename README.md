# FIAP — Gen AI Front-End Engineering

Repositório com os materiais, exercícios e projetos desenvolvidos durante o curso de **Engenharia de Front-End para IA Generativa** na FIAP.

O curso aborda a construção de interfaces inteligentes com **Streamlit** e **Gradio**, cobrindo desde os fundamentos de UX para IA até arquitetura modular, autenticação, integração com NLP e deploy.

---

## Conteúdo por Aula

| Aula | Tema | Tecnologias |
|---|---|---|
| [Aula 01](Aula01/) | Introdução ao Streamlit | Python, Streamlit |
| [Aula 02](Aula02/) | UX e Design System para IA | Streamlit, UX Principles |
| [Aula 03](Aula03/) | Input de Dados, Estado e Callbacks | Streamlit Session State |
| [Aula 04](Aula04/) | Visualização de Dados Interativa | Streamlit, Plotly, Altair, Matplotlib, PyDeck |
| [Aula 05](Aula05/) | Caching, Performance e Conectividade | Streamlit Cache, APIs externas |
| [Aula 06](Aula06/) | Modularização de Aplicações | Arquitetura features/pipelines/providers |
| [Aula 07](Aula07/) | Autenticação e Sessão | Streamlit Auth, pipelines de auth |
| [Aula 08](Aula08/) | Introdução ao Gradio | Python, Gradio |
| [Aula 09](Aula09/) | Gradio — UX, Latência e Streaming | Gradio, Streaming de resposta |
| [Aula 10](Aula10/) | Gráficos avançados com Streamlit | Streamlit Charts |

---

## Checkpoints e Projetos

### CheckPoint 1 — Generative AI Front-End
Aplicação com modelo de **Autoencoder Variacional (VAE)** treinado para reconstrução de imagens de pneumonia.
- Stack: Python, Streamlit, TensorFlow/Keras
- Inclui modelo treinado (`vae_pneumonia.weights.h5`) e pipeline de inferência

### CheckPoint 2 — NLP Front-End
Aplicação de **análise de notícias com NLP** — scraping, processamento de linguagem natural e visualização de resultados.
- Stack: Python, Streamlit, NLP pipeline
- Arquitetura modular: features / pipelines / providers / state / ui

### Sprint de Referência
Aplicação completa de **gestão de equipamentos e sensores IoT** com dashboard interativo.
- Stack: Python, Streamlit
- Módulos: cadastro, dashboard, equipamentos, sensores

---

## Arquitetura Adotada (Aulas 06+)

A partir da Aula 06 o curso introduz uma arquitetura modular inspirada em padrões de aplicações profissionais:

```
app.py                  ← entry point
├── features/           ← páginas da aplicação
│   └── nome_feature/
│       └── page.py
├── pipelines/          ← lógica de negócio e orquestração
├── providers/          ← acesso a dados e serviços externos
├── state/              ← gerenciamento de estado da sessão
└── ui/                 ← componentes visuais reutilizáveis
```

---

## Tecnologias

- **Python 3.10+**
- **Streamlit** — framework principal para interfaces de IA
- **Gradio** — framework alternativo para demos de ML
- **Plotly / Altair / Matplotlib / PyDeck** — visualização de dados
- **TensorFlow / Keras** — modelo VAE (CheckPoint 1)
- **NLP Pipeline** — scraping e análise de texto (CheckPoint 2)

---

## Instituição

**FIAP** — Faculdade de Informática e Administração Paulista  
Curso: Engenharia de Front-End para IA Generativa
