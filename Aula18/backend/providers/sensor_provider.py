import os
import sqlite3
from datetime import datetime 
from langsmith import traceable


_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "motor.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _tag_to_motor_id(tag: str) -> int:
    """Extrai o motor_id inteiro de uma TAG no formato 'MTR-NNN'."""
    try:
        return int(tag.strip().upper().replace("MTR-", ""))
    except (ValueError, AttributeError):
        return 1


def _row_to_leitura(row: sqlite3.Row, tag: str) -> dict:
    """
    Converte uma linha da tabela `leituras` no dicionário padronizado
    esperado pelos routers.
    """
    return {
        "tag":          tag,
        "timestamp":    row["timestamp"],
        "tensao_v":     380.0,                        # não está no banco
        "corrente_a":   round(row["corrente_a"],   2),
        "temp_c":       round(row["temperatura_c"], 2),
        "vibracao_mms": round(row["vibracao_mm_s"], 3),
        "rotacao_rpm":  round(row["rotacao_rpm"],   2),
        "falha":        row["falha"],
    }


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
@traceable(name="db_leitura_atual" , run_type="tool", tags=["forzy",  "sqllite", "sensores"])
def leitura_atual(tag: str) -> dict:
    """Retorna a leitura mais recente do motor na tabela `leituras`."""
    mid = _tag_to_motor_id(tag)
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM leituras WHERE motor_id = ? ORDER BY timestamp DESC LIMIT 1",
            (mid,),
        ).fetchone()
    if row:
        return _row_to_leitura(row, tag)
    # Fallback caso não existam leituras para o motor
    return {
        "tag": tag,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tensao_v": 380.0, "corrente_a": 0.0, "temp_c": 0.0,
        "vibracao_mms": 0.0, "rotacao_rpm": 0.0, "falha": 0,
    }

@traceable(name="db_historico_simulado" , run_type="tool", tags=["forzy",  "sqllite", "sensores"])
def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    """
    Retorna as últimas `n_pontos` leituras do motor ordenadas do mais
    antigo para o mais recente.
    """
    mid = _tag_to_motor_id(tag)
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leituras WHERE motor_id = ? ORDER BY timestamp DESC LIMIT ?",
            (mid, n_pontos),
        ).fetchall()
    return [_row_to_leitura(r, tag) for r in reversed(rows)]
