# =============================================================================
# providers/equipamento_provider.py — Fonte de dados dos equipamentos
#
# O que é um provider?
# --------------------
# É a ÚNICA camada da aplicação que sabe onde os dados estão armazenados.
# Pipelines e features nunca acessam o banco diretamente — eles chamam
# funções deste módulo. Isso garante que, se um dia trocarmos o banco de
# dados in-memory por PostgreSQL ou uma API REST, só este arquivo muda.
#
# Simulação vs. Produção:
# -----------------------
# Nesta sprint, os dados vivem em um dicionário Python (_DB) que existe
# enquanto o processo estiver rodando. Ao reiniciar o app, os dados voltam
# ao estado inicial.
#
# Para produção, substitua _DB por:
#   - SQLAlchemy + SQLite/PostgreSQL (banco relacional)
#   - Firebase / Supabase (banco como serviço)
#   - API REST de um backend separado
# =============================================================================

from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# _DB — banco de dados simulado em memória
#
# Estrutura: dicionário onde a chave é a TAG do equipamento (string)
# e o valor é outro dicionário com todos os campos técnicos.
# ---------------------------------------------------------------------------
_DB: dict[str, dict] = {
    "MTR-001": {
        "tag":                "MTR-001",
        "modelo":             "WEG W22 160L",
        "fabricante":         "WEG",
        "potencia_cv":        25.0,
        "tensao_v":           380,
        "corrente_nominal_a": 42.5,
        "rotacao_rpm":        1760,
        "fator_potencia":     0.86,
        "classe_isolamento":  "F",
        "ip":                 "IP55",
        "peso_kg":            145.0,
        "local":              "Planta A — Linha 1",
        "status":             "Operacional",
        "cadastrado_em":      "2024-11-10",
    },
    "MTR-002": {
        "tag":                "MTR-002",
        "modelo":             "Siemens 1LE1 200L",
        "fabricante":         "Siemens",
        "potencia_cv":        50.0,
        "tensao_v":           440,
        "corrente_nominal_a": 80.0,
        "rotacao_rpm":        1775,
        "fator_potencia":     0.88,
        "classe_isolamento":  "F",
        "ip":                 "IP55",
        "peso_kg":            280.0,
        "local":              "Planta A — Linha 2",
        "status":             "Em Manutenção",
        "cadastrado_em":      "2024-12-01",
    },
    "MTR-003": {
        "tag":                "MTR-003",
        "modelo":             "ABB M3BP 132M",
        "fabricante":         "ABB",
        "potencia_cv":        10.0,
        "tensao_v":           220,
        "corrente_nominal_a": 28.3,
        "rotacao_rpm":        1750,
        "fator_potencia":     0.82,
        "classe_isolamento":  "H",
        "ip":                 "IP66",
        "peso_kg":            68.0,
        "local":              "Planta B — Utilidades",
        "status":             "Desligado",
        "cadastrado_em":      "2025-01-15",
    },
}


def listar_todos() -> list[dict]:
    """
    Retorna todos os equipamentos cadastrados como lista de dicionários.

    Retorna cópias defensivas para que o chamador não consiga modificar
    o estado interno do _DB acidentalmente.
    """
    return [dict(eq) for eq in _DB.values()]


def buscar_por_tag(tag: str) -> Optional[dict]:
    """
    Busca um equipamento pela TAG (insensível a maiúsculas/minúsculas).

    Retorna o equipamento como dicionário, ou None se não encontrado.
    """
    entry = _DB.get(tag.strip().upper())
    return dict(entry) if entry else None


def salvar(dados: dict) -> tuple[bool, str]:
    """
    Insere um novo equipamento ou atualiza um existente (upsert).

    Valida os campos obrigatórios antes de persistir.
    Preserva a data de cadastro original em caso de atualização.

    Retorna uma tupla (sucesso: bool, mensagem: str).
    """
    # Normaliza a TAG para maiúsculas — padrão industrial
    tag = dados.get("tag", "").strip().upper()

    # Validações de campos obrigatórios
    if not tag:
        return False, "TAG de identificação é obrigatória."
    if not dados.get("modelo", "").strip():
        return False, "Modelo do equipamento é obrigatório."
    if not dados.get("fabricante", "").strip():
        return False, "Fabricante é obrigatório."

    # Verifica se é inserção ou atualização
    eh_novo = tag not in _DB

    # Em atualização, preserva a data de cadastro original
    data_cadastro = (
        _DB[tag]["cadastrado_em"]
        if not eh_novo
        else datetime.now().strftime("%Y-%m-%d")
    )

    # Persiste os dados no banco simulado
    _DB[tag] = {
        **dados,
        "tag":          tag,
        "cadastrado_em": data_cadastro,
        "status":       dados.get("status", "Operacional"),
    }

    acao = "cadastrado" if eh_novo else "atualizado"
    return True, f"Equipamento {tag} {acao} com sucesso."


def tags_disponiveis() -> list[str]:
    """
    Retorna a lista ordenada de TAGs cadastradas.
    Usada para popular dropdowns de seleção nas features.
    """
    return sorted(_DB.keys())
