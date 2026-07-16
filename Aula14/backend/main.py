# =============================================================================
# backend/main.py — Aula 14: CORS e roteamento de modelos
#
# Responsabilidade: o mesmo servidor FastAPI da Aula 12, agora com duas
# novidades desta aula: middleware de CORS e inclusão de um router versionado
# (routers/analise.py), em vez de todas as rotas soltas num único arquivo.
#
# NOVO NESTA AULA: o bloco de CORSMiddleware e o app.include_router(...).
# O restante (criação do app) já é familiar da Aula 12.
#
# Como instalar:
#   pip install fastapi uvicorn httpx
#
# Como rodar:
#   uvicorn main:app --reload --port 8000
# =============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # NOVO NESTA AULA
from routers import analise  # NOVO NESTA AULA: rotas organizadas em módulo separado

app = FastAPI(title="API de IA - FIAP", version="1.1.0")

# -----------------------------------------------------------------------------
# CORS — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) é uma regra de segurança do NAVEGADOR.
# Ela só entra em ação quando JavaScript rodando no browser tenta chamar uma
# API em outro endereço. Chamadas feitas pelo Python do Streamlit/Gradio (que
# rodam no servidor, não no navegador) NÃO são afetadas por CORS — mas assim
# que você tiver um cliente JavaScript (ex: um app React/Expo na Aula 24)
# chamando esta API diretamente do navegador, esse middleware é obrigatório.
#
# ORIGENS_PERMITIDAS é a lista de endereços que podem chamar esta API.
ORIGENS_PERMITIDAS = [
    "http://localhost:8501",          # Streamlit local (Aula 13)
    "http://localhost:7860",          # Gradio local (este arquivo)
    "https://meuapp.streamlit.app",   # Streamlit Cloud (produção, Aula 20)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
# ATENÇÃO: nunca use allow_origins=["*"] em produção — isso deixaria
# qualquer site da internet chamar sua API. É aceitável só em testes locais.


# -----------------------------------------------------------------------------
# ROUTERS — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Em vez de escrever @app.post(...) direto aqui (como na Aula 12), agora
# organizamos as rotas por assunto em routers/analise.py e as "conectamos"
# ao app principal com include_router. Isso é o mesmo espírito do
# Feature-First que já usamos no front-end desde a Aula 06.
app.include_router(analise.router, tags=["Análise"])


@app.get("/")
def raiz():
    return {"mensagem": "API de IA funcionando", "versao": app.version}
