# =============================================================================
# backend/routers/analise.py — Aula 14: roteamento de modelos (v1 e v2)
#
# Responsabilidade: reunir os endpoints de análise num único módulo,
# separados por versão (v1 = modelo leve, v2 = modelo mais robusto).
#
# NOVO NESTA AULA: a ideia de ter duas versões do MESMO endpoint, e o
# conceito de "o front escolhe qual usar".
# =============================================================================

from fastapi import APIRouter
from pydantic import BaseModel

# router é como um "mini FastAPI" — depois anexamos ele ao app principal
# (veja app.include_router em main.py)
router = APIRouter()


class EntradaTexto(BaseModel):
    texto: str


# -----------------------------------------------------------------------------
# Simulação de dois modelos diferentes.
# Em um projeto real, cada um chamaria um provider distinto (ex: um modelo
# leve local vs. um modelo mais caro/robusto na nuvem).
# -----------------------------------------------------------------------------

def _analisar_leve(texto: str) -> dict:
    """Simula um modelo leve e rápido, ideal para respostas em tempo real."""
    sentimento = "negativo" if "defeito" in texto.lower() else "positivo"
    return {"sentimento": sentimento, "confianca": 0.80, "tokens_usados": len(texto.split())}


def _analisar_robusto(texto: str) -> dict:
    """Simula um modelo mais lento e detalhado, usado quando precisão importa mais que velocidade."""
    sentimento = "negativo" if "defeito" in texto.lower() else "positivo"
    return {
        "sentimento": sentimento,
        "confianca": 0.95,               # modelo v2 é "mais confiante" na simulação
        "tokens_usados": len(texto.split()) * 2,
        "detalhes": "análise v2 considera contexto adicional",
    }


# -----------------------------------------------------------------------------
# ROTA v1 — modelo leve e rápido
# -----------------------------------------------------------------------------
@router.post("/v1/analise/sentimento")
def sentimento_v1(entrada: EntradaTexto):
    return _analisar_leve(entrada.texto)


# -----------------------------------------------------------------------------
# ROTA v2 — modelo mais robusto, retorna mais detalhes
# -----------------------------------------------------------------------------
@router.post("/v2/analise/sentimento")
def sentimento_v2(entrada: EntradaTexto):
    return _analisar_robusto(entrada.texto)
