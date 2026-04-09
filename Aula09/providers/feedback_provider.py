# =============================================================================
# providers/feedback_provider.py — Armazenamento de feedback humano
#
# Responsabilidade: persistir e recuperar os registros de avaliação do usuário.
# Em produção: substitua a lista em memória por banco de dados ou API.
# O pipeline e a UI nunca sabem como o dado é armazenado — apenas chamam
# as funções públicas deste módulo.
# =============================================================================

from datetime import datetime


# Armazenamento em memória — escopo do processo (reinicia com o app)
# Em produção: use SQLite, PostgreSQL, ou uma API de coleta de dados
_registro: list[dict] = []


def salvar(pergunta: str, resposta: str, tipo: str) -> None:
    """
    Registra uma avaliação humana com contexto completo.

    Parâmetros:
        pergunta: mensagem que originou a resposta avaliada
        resposta: texto completo gerado pelo modelo
        tipo:     "positivo" ou "negativo"
    """
    _registro.append({
        "timestamp": datetime.now().isoformat(),
        "pergunta": pergunta,
        "resposta": resposta,
        "feedback": tipo,
    })


def resumo() -> dict:
    """
    Retorna um resumo agregado do feedback acumulado.
    Útil para exibir métricas de qualidade na interface.

    Retorna um dicionário com:
        total:     número total de avaliações
        positivos: contagem de feedbacks positivos
        negativos: contagem de feedbacks negativos
    """
    total = len(_registro)
    positivos = sum(1 for r in _registro if r["feedback"] == "positivo")
    return {
        "total": total,
        "positivos": positivos,
        "negativos": total - positivos,
    }


def todos() -> list[dict]:
    """
    Retorna uma cópia de todos os registros.
    Cópia defensiva: o chamador não pode modificar o estado interno.
    """
    return list(_registro)
