# =============================================================================
# backend/pipelines/news_pipeline.py — Aula 15
#
# Responsabilidade: orquestrar o fluxo de dados (ETL), exatamente como o
# pipelines/news_pipeline.py da Aula 06 do Semestre 1 — só que agora ele mora
# dentro do back-end FastAPI em vez de ser chamado direto pelo Streamlit.
#
# REAPROVEITADO DA AULA 06 (semestre 1), com pequenos ajustes de formato de
# retorno para bater com o contrato Pydantic (ResultadoNoticia) desta aula.
# =============================================================================

from providers.scraper_nlp_provider import coleta, preparacao, analise_local


def processar_noticia(url: str = None, texto: str = None) -> dict:
    """
    Pipeline completo: coleta (se vier URL) -> limpeza -> análise NLP.

    Args:
        url: endereço da notícia a ser raspada (scraping). Opcional.
        texto: texto já pronto, colado pelo usuário. Opcional.
              Pelo menos um dos dois deve ser informado (isso já foi
              validado no router antes de chegar aqui).

    Returns:
        dict no formato esperado por ResultadoNoticia: resumo, sentimento,
        entidades e confianca.
    """
    # -------------------------------------------------------------------
    # 1) COLETA (só roda scraping se o usuário mandou uma URL)
    # -------------------------------------------------------------------
    if texto:
        conteudo_bruto = texto
    else:
        df_bruto = coleta([url])
        if df_bruto.empty:
            return {"resumo": "", "sentimento": "indefinido", "entidades": [], "confianca": 0.0}
        conteudo_bruto = df_bruto.iloc[0]["texto_bruto"]

    # -------------------------------------------------------------------
    # 2) LIMPEZA / PREPARAÇÃO
    # -------------------------------------------------------------------
    import pandas as pd
    df_final = preparacao(pd.DataFrame([{"url": url or "texto-colado", "texto_bruto": conteudo_bruto}]))

    if df_final.empty:
        return {"resumo": "", "sentimento": "indefinido", "entidades": [], "confianca": 0.0}

    # -------------------------------------------------------------------
    # 3) ANÁLISE NLP
    # -------------------------------------------------------------------
    resultado_analise = analise_local(df_final)

    # -------------------------------------------------------------------
    # 4) FORMATA NO CONTRATO ESPERADO PELO ResultadoNoticia (Pydantic)
    # -------------------------------------------------------------------
    return {
        "resumo": resultado_analise["summary"],
        "sentimento": resultado_analise["overall_sentiment"],
        "entidades": list(resultado_analise.get("themes", [])),
        "confianca": abs(resultado_analise["polarity_val"]),
    }
