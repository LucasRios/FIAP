# =============================================================================
# main.py — Ponto de entrada do back-end
#
# Cria o app FastAPI, configura CORS e inclui os routers.
# =============================================================================

from dotenv import load_dotenv
load_dotenv()  # precisa vir ANTES de importar auth/routers, que leem os.getenv no import

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import equipamentos, plantas, sensores

app = FastAPI(title="Forzy Digital Twin API", version="1.0.0")

# CORS — o Gradio local roda em http://localhost:7860 por padrão
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7860"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(equipamentos.router, prefix="/v1")
app.include_router(plantas.router,      prefix="/v1")
app.include_router(sensores.router,     prefix="/v1")


@app.get("/")
def raiz():
    return {"status": "ok", "servico": "Forzy Digital Twin API"}
