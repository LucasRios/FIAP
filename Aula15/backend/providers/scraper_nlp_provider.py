# =============================================================================
# backend/providers/scraper_nlp_provider.py — Aula 15
#
# REAPROVEITADO DA AULA 06 (Semestre 1) — o conteúdo de scraping e análise
# NLP não muda. O que muda é ONDE ele roda: antes vivia dentro do processo do
# Streamlit; agora vive dentro do back-end FastAPI, chamado pelo pipeline
# (backend/pipelines/news_pipeline.py) e nunca mais diretamente pelo front-end.
#
# PROVIDER DE COLETA E ANÁLISE NLP — Scraping, limpeza e análise de sentimento
# via léxico local (sem dependência de API externa).
#
# INSTALAÇÃO — rode esses comandos no terminal antes de executar:
#   pip install requests beautifulsoup4 textblob nltk scikit-learn matplotlib pandas
# =============================================================================

import requests
import pandas as pd
import re
import matplotlib
import nltk

from bs4 import BeautifulSoup
from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# Matplotlib em modo não-interativo: evita erro de "sem display" no servidor
# (aqui não precisamos mais de st.pyplot — o back-end não desenha telas).
matplotlib.use('Agg')

# Download de recursos essenciais do NLTK (execução local)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)


# =============================================================================
# ETAPA 1 — Coleta via Scraping (RPA com requests + BeautifulSoup)
# =============================================================================
def coleta(urls: list) -> pd.DataFrame:
    """
    Faz scraping das URLs informadas e extrai o conteúdo textual relevante.

    Args:
        urls (list): Lista de URLs a coletar.

    Returns:
        pd.DataFrame: Colunas ["url", "texto_bruto"] com o conteúdo coletado.
    """
    dataset_bruto = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for url in urls:
        try:
            print(f"[RPA] Coletando: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            fragments = [tag.text.strip() for tag in soup.find_all(['p', 'h1', 'h2'])]
            content = " ".join([f for f in fragments if len(f) > 30])

            if len(content) > 100:
                dataset_bruto.append({"url": url, "texto_bruto": content})

        except Exception as e:
            print(f"[Erro] Falha em {url}: {e}")

    return pd.DataFrame(dataset_bruto)


# =============================================================================
# ETAPA 2 — Preparação e Limpeza do Texto
# =============================================================================
def preparacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza o texto bruto e remove duplicatas.

    Args:
        df (pd.DataFrame): DataFrame com coluna "texto_bruto".

    Returns:
        pd.DataFrame: DataFrame com coluna "texto_limpo" adicionada.
    """
    if df.empty:
        return df

    def limpar_texto(texto):
        texto = texto.lower()
        texto = re.sub(r'[^a-zá-ú0-9\s\.]', '', texto)
        return re.sub(r'\s+', ' ', texto).strip()

    df['texto_limpo'] = df['texto_bruto'].apply(limpar_texto)
    df = df.drop_duplicates(subset=['texto_limpo'])
    df = df[df['texto_limpo'].str.len() > 30]  # limite reduzido p/ funcionar com texto colado curto
    return df


# =============================================================================
# ETAPA 3 — Análise NLP Local (Sentimento + TF-IDF + Sumarização)
# =============================================================================
def analise_local(df: pd.DataFrame) -> dict:
    """
    Executa análise NLP completa sobre o DataFrame limpo:
      1. Sentimento via TextBlob (polaridade léxica)
      2. Extração de temas via TF-IDF
      3. Sumarização extrativa simples

    Args:
        df (pd.DataFrame): DataFrame com coluna "texto_limpo".

    Returns:
        dict: overall_sentiment, polarity_val, themes, summary, distribution
    """
    texto_completo = " ".join(df['texto_limpo'].tolist())

    sentiment_scores = [TextBlob(txt).sentiment.polarity for txt in df['texto_limpo']]
    avg_polarity = sum(sentiment_scores) / len(sentiment_scores)

    overall = (
        "Positivo" if avg_polarity > 0.05 else
        "Negativo" if avg_polarity < -0.05 else
        "Neutro"
    )

    try:
        vectorizer = TfidfVectorizer(max_features=10, stop_words=stopwords.words('portuguese'))
        vectorizer.fit_transform(df['texto_limpo'])
        temas = list(vectorizer.get_feature_names_out())
    except ValueError:
        # Texto curto demais para extrair temas — não é um erro fatal
        temas = []

    sentencas = sent_tokenize(texto_completo)
    resumo = " ".join(sentencas[:3]) + ("..." if len(sentencas) > 3 else "")

    return {
        "overall_sentiment": overall,
        "polarity_val": avg_polarity,
        "themes": temas,
        "summary": resumo,
        "distribution": {
            "positive": len([s for s in sentiment_scores if s > 0.05]) / len(sentiment_scores) * 100,
            "neutral": len([s for s in sentiment_scores if -0.05 <= s <= 0.05]) / len(sentiment_scores) * 100,
            "negative": len([s for s in sentiment_scores if s < -0.05]) / len(sentiment_scores) * 100,
        }
    }
