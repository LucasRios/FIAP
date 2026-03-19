# =============================================================================
# providers/scraper_provider.py — Extração de texto de páginas web
#
# Responsabilidade: fazer o scraping de uma URL e retornar o texto limpo.
# Esta camada ISOLA a dependência de requests + BeautifulSoup do restante
# da aplicação. Se trocar a lib de scraping, só este arquivo muda.
# =============================================================================

import requests
from bs4 import BeautifulSoup 
 
def scrape_news(url: str) -> str:
    """
    Faz o download e parsing de uma página de notícia.

    Fluxo:
      1. requests.get() → baixa o HTML da URL
      2. BeautifulSoup → faz o parse do HTML
      3. soup.find_all("p") → extrai somente as tags <p> (parágrafos)
      4. Junta tudo em uma única string de texto limpo

    Args:
        url (str): URL completa da notícia (ex: "https://g1.globo.com/...")

    Returns:
        str: Texto completo extraído dos parágrafos da página.
             Retorna string vazia em caso de erro.
    """

    try:
        # Faz a requisição HTTP com timeout de 10 segundos
        response = requests.get(url, timeout=10)

        # Lança exceção se o status HTTP for 4xx ou 5xx
        response.raise_for_status()

        # Parse do HTML com o parser padrão do Python
        soup = BeautifulSoup(response.text, "html.parser")

        # Extrai texto de todas as tags <p> (parágrafos)
        # Essa heurística funciona bem para a maioria dos portais de notícia
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        return text

    except requests.exceptions.RequestException as e: 
        return ""