# =============================================================================
# backend/pipelines/news_pipeline.py — Aula 17: instrumentando o pipeline
# inteiro, não só o provider.
#
# Responsabilidade: mesma orquestração ETL da Aula 15, mas agora CADA etapa
# tem seu próprio @traceable. O LangSmith monta uma árvore: você vê o tempo
# total E também onde, dentro do pipeline, o tempo está sendo gasto.
#
# NOVO NESTA AULA: @traceable em cada função (não só na função principal),
# as tags=[...] no pipeline principal, e o session_id passando por todas
# as camadas até chegar ao provider.
# =============================================================================

from langsmith import traceable  # NOVO NESTA AULA
from providers import scraper_nlp_provider, modelo_provider


# -----------------------------------------------------------------------------
# @traceable NO NÍVEL DO PIPELINE — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# tags=[...] são rótulos livres que você pode usar para filtrar traces no
# dashboard do LangSmith (ex: "me mostre só os traces de produção").
@traceable(name="pipeline_noticia", tags=["producao", "v1"])
def processar_noticia(url: str = None, texto: str = None, session_id: str = None) -> dict:
    """
    Pipeline completo: obter conteúdo -> extrair entidades -> analisar com modelo.
    Cada etapa abaixo tem seu próprio trace filho, visível no dashboard.

    Args:
        url: URL da notícia (opcional).
        texto: texto já pronto (opcional).
        session_id: identificador da sessão — propagado a cada etapa para
                    conectar os traces com o usuário que originou a chamada.
    """
    # Etapa 1 — Obter o texto (do scraping ou já pronto)
    conteudo = _obter_conteudo(url=url, texto=texto, session_id=session_id)
    if not conteudo:
        return {"erro": "Não foi possível obter o conteúdo."}

    # Etapa 2 — Extrair entidades (pré-processamento)
    entidades = _extrair_entidades(conteudo, session_id=session_id)

    # Etapa 3 — Análise final com o modelo de IA
    analise = modelo_provider.analisar_completo(conteudo, entidades, session_id=session_id)

    return {
        "resumo": analise["resumo"],
        "sentimento": analise["sentimento"],
        "entidades": entidades,
        "confianca": analise["confianca"],
        "tokens_usados": analise["tokens_usados"],
    }


# -----------------------------------------------------------------------------
# Cada etapa interna também é @traceable — NOVO NESTA AULA
# -----------------------------------------------------------------------------
@traceable(name="obter_conteudo")
def _obter_conteudo(url: str = None, texto: str = None, session_id: str = None) -> str | None:
    if texto:
        return texto
    if url:
        return scraper_nlp_provider.raspar_url(url)
    return None


@traceable(name="extrair_entidades")
def _extrair_entidades(texto: str, session_id: str = None) -> list[str]:
    return scraper_nlp_provider.extrair_entidades(texto)
