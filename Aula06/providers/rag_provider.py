# =============================================================================
# providers/rag_provider.py — Recuperação de contexto (RAG simplificado)
#
# Responsabilidade: receber o texto bruto e retornar os trechos mais
# relevantes para alimentar o modelo LLM.
#
# O que é RAG? (Retrieval-Augmented Generation)
#   Em vez de mandar TODO o texto para o modelo (o que pode ser longo e caro),
#   o RAG seleciona apenas os trechos mais relevantes. Na vida real usaríamos
#   embeddings + banco vetorial (ex: FAISS, Chroma). Aqui usamos uma versão
#   simplificada apenas para demonstrar o conceito na pipeline. 
# =============================================================================
 
def run_rag(text: str) -> str:
    """
    Versão simplificada de RAG: seleciona os primeiros N trechos do texto.

    Em uma implementação real, este provider:
      1. Dividiria o texto em chunks de tamanho fixo
      2. Geraria embeddings para cada chunk (ex: sentence-transformers)
      3. Armazenaria em um banco vetorial (FAISS, Chroma, Pinecone...)
      4. Buscaria os chunks mais similares à query do usuário

    Para este projeto educacional, simulamos o passo de "seleção de contexto"
    pegando as primeiras 10 sentenças — que geralmente contêm o lide da notícia.

    Args:
        text (str): Texto bruto extraído pelo scraper

    Returns:
        str: Contexto reduzido a ser enviado ao modelo LLM
    """

    if not text:
        return ""

    # Divide por ponto final e pega as 10 primeiras sentenças
    # Isso simula a "recuperação" dos trechos mais relevantes
    chunks = [chunk.strip() for chunk in text.split(".") if chunk.strip()]
    selected_chunks = chunks[:10]

    # Reconstrói o contexto como texto único
    context = ". ".join(selected_chunks) + "."

    return context