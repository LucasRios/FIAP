# =============================================================================
# pipelines/formatacao.py — Regras de escrita de números, unidades e limites
#
# Conteúdo também faz parte do design system: "92.99" e "93,0 °C" carregam
# o mesmo dado, mas só o segundo é lido de relance por um operador brasileiro.
# Centralizar a formatação garante que todas as telas escrevam igual.
# =============================================================================

# Limites ISO 10816 usados para EXPLICAR o alarme e desenhar as linhas de
# referência. A classificação em si continua no back-end.
# Exercício proposto: buscar estes valores de um endpoint GET /v1/sensores/limites.
LIMITES = {
    "temp_c": {"aviso": 75.0, "critico": 90.0},
    "vibracao_mms": {"aviso": 4.5, "critico": 7.1},
}

# Nome, unidade e casas decimais de cada grandeza — uma única definição.
GRANDEZAS = {
    "temp_c":       {"nome": "Temperatura", "unidade": "°C",   "casas": 1, "chave_sev": "severidade_temp"},
    "vibracao_mms": {"nome": "Vibração",    "unidade": "mm/s", "casas": 2, "chave_sev": "severidade_vibracao"},
    "corrente_a":   {"nome": "Corrente",    "unidade": "A",    "casas": 1, "chave_sev": None},
    "tensao_v":     {"nome": "Tensão",      "unidade": "V",    "casas": 0, "chave_sev": None},
    "rotacao_rpm":  {"nome": "Rotação",     "unidade": "RPM",  "casas": 0, "chave_sev": None},
}


def numero(valor: float | int | None, casas: int = 1) -> str:
    """Formata no padrão brasileiro: vírgula decimal e ponto de milhar (1.760,5)."""
    if valor is None:
        return "—"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def com_unidade(chave: str, valor: float | None) -> str:
    """Valor formatado com a unidade da grandeza (ex.: '93,0 °C')."""
    g = GRANDEZAS[chave]
    return f"{numero(valor, g['casas'])} {g['unidade']}"


def hora(timestamp: str) -> str:
    """'2026-10-02 22:12:00' -> '22:12'. Em tela pequena, a data repetida é ruído."""
    return timestamp[11:16] if len(timestamp) >= 16 else timestamp
