# =============================================================================
# pipelines/news_pipeline.py — Orquestração do fluxo de análise
#
# Responsabilidade: conectar os providers em sequência, formando a pipeline
# completa de processamento de uma notícia.
#
# Este arquivo NÃO conhece Streamlit — é Python puro. Isso facilita testes
# unitários e reaproveitamento da lógica fora do contexto da UI.
#
# Fluxo:
#   URL → [Scraper] → texto bruto
#              ↓
#           [RAG] → contexto reduzido
#              ↓
#    [LLM: resumo + sentimento] → resultado final
# =============================================================================

from providers.scraper_provider import scrape_news
from providers.rag_provider import run_rag
from providers.llm_provider import summarize_text, analyze_sentiment


def analyze_news(url: str, model: str) -> dict:
    """
    Executa a pipeline completa de análise de uma notícia.

    Args:
        url   (str): URL da notícia a ser analisada
        model (str): Modelo LLM selecionado pelo usuário

    Returns:
        dict com as chaves:
            - "article"   (str):  Texto bruto extraído da página
            - "context"   (str):  Contexto selecionado pelo RAG
            - "summary"   (str):  Resumo gerado pelo LLM
            - "sentiment" (dict): Resultado da análise de sentimento
                                  {"label": str, "score": float, "emoji": str}
    """

    # Passo 1: Scraping — faz download e extrai texto da página
    article = scrape_news(url)

    # Passo 2: RAG — seleciona os trechos mais relevantes do texto
    context = run_rag(article)

    # Passo 3a: LLM → gera o resumo da notícia
    summary = summarize_text(context, model)

    # Passo 3b: NLP → analisa o sentimento do texto
    sentiment = analyze_sentiment(context)

    return {
        "article":   article,
        "context":   context,
        "summary":   summary,
        "sentiment": sentiment,
    }