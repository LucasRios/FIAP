from providers.scraper_provider import scrape_news
from providers.rag_provider import run_rag
from providers.llm_provider import summarize_text

def analyze_news(url, model):

    article = scrape_news(url)

    context = run_rag(article)

    summary = summarize_text(context, model)

    return {
        "article": article,
        "summary": summary
    }