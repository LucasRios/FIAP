# =============================================================================
# backend/routers/feedback.py — Aula 17: enviando feedback do usuário ao LangSmith
#
# Responsabilidade: receber o like/dislike do front-end e anexá-lo ao trace
# exato que gerou aquela resposta, usando o trace_id devolvido em
# noticias.py.
#
# NOVO NESTA AULA: este arquivo inteiro — é o fechamento do ciclo de
# observabilidade: capturamos o trace, devolvemos o ID ao front, e agora
# recebemos de volta a avaliação humana sobre aquele trace específico.
# =============================================================================

from fastapi import APIRouter, Security
from pydantic import BaseModel
from langsmith import Client
from main import verificar_chave

router = APIRouter()
ls_client = Client()  # cliente do LangSmith, usa as mesmas variáveis de ambiente


class EntradaFeedback(BaseModel):
    trace_id: str               # o ID do trace que queremos avaliar
    aprovado: bool               # True = like, False = dislike
    comentario: str | None = None


@router.post("/feedback")
def registrar_feedback(feedback: EntradaFeedback, _: str = Security(verificar_chave)):
    # create_feedback anexa uma avaliação (score de 0 a 1) a um trace
    # específico do LangSmith, identificado por run_id.
    ls_client.create_feedback(
        run_id=feedback.trace_id,
        key="aprovacao_usuario",
        score=1.0 if feedback.aprovado else 0.0,
        comment=feedback.comentario,
    )
    return {"status": "registrado"}
