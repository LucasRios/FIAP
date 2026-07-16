# =============================================================================
# backend/providers/scraper_nlp_provider.py — Aula 17
#
# Responsabilidade: funções auxiliares de scraping e extração de entidades,
# usadas pelo pipeline instrumentado (news_pipeline.py). São versões
# simplificadas, focadas em servir de exemplo para o tracing desta aula —
# a versão completa de scraping+NLP está na Aula 06/15.
# =============================================================================

import requests
from bs4 import BeautifulSoup


def raspar_url(url: str) -> str | None:
    """Faz scraping simples de uma URL e retorna o texto extraído."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(url, headers=headers, timeout=15)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        paragrafos = [p.get_text(strip=True) for p in soup.find_all(["p", "h1", "h2"])]
        return " ".join(p for p in paragrafos if len(p) > 30) or None
    except Exception:
        return None


def extrair_entidades(texto: str) -> list[str]:
    """
    Extração de entidades simplificada para fins didáticos: procura por
    palavras capitalizadas como aproximação de nomes próprios.
    Em um projeto real, aqui entraria uma biblioteca de NER (ex: spaCy).
    """
    palavras = texto.split()
    candidatas = {p.strip(".,!?") for p in palavras if p[:1].isupper() and len(p) > 3}
    return sorted(candidatas)[:10]
