# =============================================================================
# providers/llm_provider.py — Integração com o modelo de linguagem (LLM)
#
# Responsabilidade: receber contexto processado e retornar resumo e análise
# de sentimento. Este provider ISOLA a dependência do modelo — se trocar de
# OpenAI para Gemini, só este arquivo muda.
#
# SIMULAÇÃO: Neste projeto as funções simulam as respostas do modelo com
# texto fixo + delay, para focar no aprendizado da arquitetura Streamlit.
# Para integrar um LLM real, substitua o corpo das funções pela chamada
# à API correspondente (openai.chat.completions.create, etc.)
# =============================================================================
 
import time
import random

 
def summarize_text(context: str, model: str) -> str:
    """
    Gera um resumo do contexto usando o modelo especificado.

    Em produção, aqui entraria a chamada real ao LLM:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Resuma: {context}"}]
        )
        return response.choices[0].message.content

    Args:
        context (str): Texto reduzido pelo RAG provider
        model   (str): Identificador do modelo escolhido nas configurações

    Returns:
        str: Resumo gerado pelo modelo
    """

    # Simula o tempo de processamento do modelo
    time.sleep(1)

    # Resumo simulado — em produção viria da API do LLM
    return (
        f"[Modelo: {model.upper()}] Esta notícia aborda um tema de grande relevância "
        "para o cenário atual. Os principais pontos destacados incluem impactos "
        "econômicos, desdobramentos políticos e repercussão nas redes sociais. "
        "Especialistas ouvidos pela reportagem divergem sobre as consequências "
        "de longo prazo, mas concordam que o assunto demanda atenção imediata "
        "da sociedade e das autoridades competentes."
    )

 
def analyze_sentiment(context: str) -> dict:
    """
    Analisa o sentimento predominante no texto da notícia.

    Retorna um dicionário padronizado com:
      - label (str):  rótulo do sentimento em português
      - score (float): confiança do modelo (0.0 a 1.0)
      - emoji (str):  emoji representativo para exibição na UI

    Em produção, usaríamos um modelo de NLP (ex: HuggingFace Transformers):
        from transformers import pipeline
        nlp = pipeline("sentiment-analysis", model="neuralmind/bert-base-portuguese-cased")
        result = nlp(context[:512])[0]

    Args:
        context (str): Texto ou contexto da notícia

    Returns:
        dict: {"label": str, "score": float, "emoji": str}
    """

    # Simula tempo de inferência do modelo de NLP
    time.sleep(0.5)

    # Possíveis resultados simulados — em produção viria do modelo real
    # Usamos random para variar o resultado a cada nova URL analisada. 
    sentiments = [
        {"label": "Positivo",  "score": round(random.uniform(0.75, 0.97), 2), "emoji": "😊"},
        {"label": "Negativo",  "score": round(random.uniform(0.70, 0.95), 2), "emoji": "😟"},
        {"label": "Neutro",    "score": round(random.uniform(0.60, 0.85), 2), "emoji": "😐"},
        {"label": "Alarmista", "score": round(random.uniform(0.65, 0.90), 2), "emoji": "😰"},
    ]

    return random.choice(sentiments)