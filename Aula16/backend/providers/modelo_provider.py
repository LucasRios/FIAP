# =============================================================================
# backend/providers/modelo_provider.py — Aula 16: primeiro trace com LangSmith
#
# Responsabilidade: chamar o modelo de IA (aqui, a Anthropic) e, nesta aula,
# capturar automaticamente cada chamada num "trace" — um registro completo de
# entrada, saída, tempo gasto e tokens usados — para conseguirmos enxergar a
# "caixa preta" da IA.
#
# NOVO NESTA AULA: o decorator @traceable e as 3 variáveis de ambiente do
# LangSmith. É só ISSO que muda em relação a um provider comum — o resto
# (chamar o modelo) já é familiar de aulas anteriores.
#
# Como instalar:
#   pip install anthropic langsmith
#
# Como configurar (variáveis de ambiente — nunca hardcoded no código):
#   LANGCHAIN_API_KEY=sua-chave-langsmith
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_PROJECT=sprint-fiap
# =============================================================================

import os
import anthropic
from langsmith import traceable  # NOVO NESTA AULA

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DO LANGSMITH — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Repare: NÃO importamos LangChain aqui. O LangSmith funciona sozinho, com
# qualquer SDK de LLM (Anthropic, OpenAI, etc) — basta essas 3 variáveis.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "sprint-fiap")
# LANGCHAIN_API_KEY deve vir do ambiente real (ex: .env), nunca escrito aqui.

client = anthropic.Anthropic()


# -----------------------------------------------------------------------------
# @traceable — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Este decorator "embrulha" a função abaixo. Toda vez que analisar(...) for
# chamada, o LangSmith registra automaticamente:
#   - os parâmetros de entrada (texto, session_id)
#   - o tempo de execução
#   - a resposta do modelo
#   - quantos tokens foram usados
#   - qualquer erro/exceção que acontecer
#
# name="analisar_sentimento" é só o nome que vai aparecer no dashboard do
# LangSmith — ajuda a identificar esta chamada entre várias outras.
@traceable(name="analisar_sentimento")
def analisar(texto: str, session_id: str = None) -> dict:
    """
    Chama o modelo Claude para classificar o sentimento de um texto.

    Args:
        texto: o texto a ser analisado.
        session_id: identificador da sessão do usuário (opcional). Não é
                    usado na chamada ao modelo, mas o LangSmith usa este
                    parâmetro para aparecer no trace — útil para depois
                    filtrar "todos os traces desta sessão" no dashboard.

    Returns:
        dict com sentimento, confiança (fixa nesta versão simplificada) e
        tokens_usados (soma de tokens de entrada e saída).
    """
    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=(
            "Classifique o sentimento do texto como 'positivo', 'negativo' "
            "ou 'neutro'. Responda apenas com a palavra."
        ),
        messages=[{"role": "user", "content": texto}],
    )

    sentimento = resposta.content[0].text.strip().lower()

    return {
        "sentimento": sentimento,
        "confianca": 0.9,  # simplificado nesta aula — em produção viria do modelo
        "tokens_usados": resposta.usage.input_tokens + resposta.usage.output_tokens,
    }


# -----------------------------------------------------------------------------
# Depois de rodar esta função uma vez, acesse:
#   https://smith.langchain.com
# e veja o trace gerado — input, output, latência, tokens, custo estimado.
# =============================================================================
