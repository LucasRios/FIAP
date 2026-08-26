# =============================================================================
# providers/equipamento_provider.py — Fonte de dados dos equipamentos
#
# O que é um provider?
# --------------------
# É a ÚNICA camada da aplicação que sabe onde os dados estão armazenados.
# Routers nunca acessam o banco diretamente — eles chamam funções deste módulo.
#
# Banco de dados:
# ---------------
# Lê da tabela `motores` do arquivo motor.db (SQLite 3).
# Schema: motor_id (PK), fabricante, modelo, potencia_kw, ano_instalacao.
#
# Campos sem equivalente no banco (tensao_v, corrente_nominal_a, etc.) são
# calculados ou preenchidos com defaults técnicos razoáveis para que o
# restante da aplicação continue funcionando sem alterações.
# =============================================================================

import os
import sqlite3
from datetime import datetime
from typing import Optional

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "motor.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _row_to_dict(row: sqlite3.Row) -> dict:
    """
    Converte uma linha da tabela `motores` no dicionário padronizado
    esperado pelo restante da aplicação.

    Campos ausentes no banco recebem valores padrão derivados dos dados
    disponíveis (ex: corrente estimada a partir da potência).
    """
    mid = row["motor_id"]
    pkw = row["potencia_kw"]

    return {
        "tag":                f"MTR-{mid:03d}",
        "modelo":             row["modelo"],
        "fabricante":         row["fabricante"],
        # Conversão kW → cv  (1 kW = 1,34102 cv)
        "potencia_cv":        round(pkw * 1.34102, 1),
        # Campos não presentes no banco — defaults técnicos
        "tensao_v":           380,
        "corrente_nominal_a": round(pkw * 1.77, 1),   # I ≈ P / (√3 · V · FP)
        "rotacao_rpm":        1760,
        "fator_potencia":     0.86,
        "classe_isolamento":  "F",
        "ip":                 "IP55",
        "peso_kg":            0.0,
        "local":              "",
        "status":             "Operacional",
        "cadastrado_em":      str(row["ano_instalacao"]),
    }


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def listar_todos() -> list[dict]:
    """Retorna todos os equipamentos cadastrados como lista de dicionários."""
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM motores ORDER BY motor_id").fetchall()
    return [_row_to_dict(r) for r in rows]


def buscar_por_tag(tag: str) -> Optional[dict]:
    """
    Busca um equipamento pela TAG (ex: 'MTR-005').
    Retorna None se não encontrado.
    """
    try:
        mid = int(tag.strip().upper().replace("MTR-", ""))
    except (ValueError, AttributeError):
        return None
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM motores WHERE motor_id = ?", (mid,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def salvar(dados: dict) -> tuple[bool, str]:
    """
    Insere ou atualiza um equipamento na tabela `motores` (upsert).

    Persiste apenas os campos suportados pelo banco:
    motor_id, fabricante, modelo, potencia_kw, ano_instalacao.
    O ano_instalacao é preservado em atualizações e definido como o
    ano corrente em inserções.

    Retorna (sucesso: bool, mensagem: str).
    """
    tag = dados.get("tag", "").strip().upper()
    if not tag:
        return False, "TAG de identificação é obrigatória."
    if not dados.get("modelo", "").strip():
        return False, "Modelo do equipamento é obrigatório."
    if not dados.get("fabricante", "").strip():
        return False, "Fabricante é obrigatório."

    try:
        mid = int(tag.replace("MTR-", ""))
    except ValueError:
        return False, f"TAG inválida: {tag}. Use o formato MTR-NNN."

    # Converte cv → kW para persistência
    potencia_kw = round((dados.get("potencia_cv") or 0) / 1.34102, 2)

    with _conn() as conn:
        existing = conn.execute(
            "SELECT ano_instalacao FROM motores WHERE motor_id = ?", (mid,)
        ).fetchone()
        eh_novo = existing is None
        ano = datetime.now().year if eh_novo else existing["ano_instalacao"]

        conn.execute(
            """INSERT OR REPLACE INTO motores
               (motor_id, fabricante, modelo, potencia_kw, ano_instalacao)
               VALUES (?, ?, ?, ?, ?)""",
            (mid, dados["fabricante"], dados["modelo"], potencia_kw, ano),
        )

    acao = "cadastrado" if eh_novo else "atualizado"
    return True, f"Equipamento {tag} {acao} com sucesso."


def tags_disponiveis() -> list[str]:
    """Retorna a lista ordenada de TAGs cadastradas."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT motor_id FROM motores ORDER BY motor_id"
        ).fetchall()
    return [f"MTR-{r['motor_id']:03d}" for r in rows]
