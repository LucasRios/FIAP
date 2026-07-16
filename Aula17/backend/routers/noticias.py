# =============================================================================
# backend/routers/noticias.py — Aula 17: propagando o session_id do header
#
# Responsabilidade: receber a requisição HTTP e repassar o session_id (que
# vem de um header customizado) até o pipeline, para que os traces no
# LangSmith fiquem conectados à sessão do usuário no front-end.
#
# NOVO NESTA AULA: o parâmetro Header(None), que lê X-Session-Id da
# requisição, e o retorno do trace_id junto com o resultado.
# =============================================================================

from fastapi import APIRouter, Security, Header
from typing import Optional
from pydantic import BaseModel
from pipelines.news_pipeline import processar_noticia
from langsmith import get_current_run_tree  # NOVO NESTA AULA
from main import verificar_chave

router = APIRouter()


class EntradaNoticia(BaseModel):
    url: str | None = None
    texto: str | None = None


@router.post("/noticias/analisar")
def analisar_noticia(
    entrada: EntradaNoticia,
    _: str = Security(verificar_chave),
    # Header(None) lê o header HTTP "X-Session-Id" enviado pelo front-end.
    # Se o front não enviar, o valor é None — não quebra a requisição.
    x_session_id: Optional[str] = Header(None),
):
    # O session_id atravessa pipeline -> etapas -> provider, aparecendo em
    # TODOS os traces relacionados a esta chamada.
    resultado = processar_noticia(
        url=entrada.url,
        texto=entrada.texto,
        session_id=x_session_id,
    )

    # -------------------------------------------------------------------
    # NOVO NESTA AULA: captura o ID do trace atual do LangSmith e devolve
    # ao front-end. É esse trace_id que o front vai usar depois para
    # enviar o feedback (like/dislike) associado exatamente a esta chamada.
    # -------------------------------------------------------------------
    run_tree = get_current_run_tree()
    run_id = str(run_tree.id) if run_tree else None

    return {**resultado, "trace_id": run_id}
