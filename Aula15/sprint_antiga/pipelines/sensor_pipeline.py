# =============================================================================
# pipelines/sensor_pipeline.py — Lógica de negócio dos dados de sensores
#
# Responsabilidades deste pipeline:
#   1. Buscar o status atual do equipamento para usar o perfil correto
#   2. Solicitar leituras ao provider de sensores
#   3. Classificar cada grandeza por severidade (normal / aviso / crítico)
#   4. Formatar os dados para exibição nos componentes Gradio (Markdown e Dataframe)
#
# A classificação de severidade usa os limites da norma ISO 10816
# para vibração e limites operacionais típicos para as demais grandezas.
# =============================================================================

import providers.sensor_provider as sensor_provider
import providers.equipamento_provider as eq_provider


# ---------------------------------------------------------------------------
# _LIMITES — thresholds para classificação de severidade
#
# Formato: {"nome_grandeza": {"aviso": valor, "critico": valor}}
# Grandezas não listadas aqui são sempre classificadas como "normal".
#
# Referências:
#   Vibração — ISO 10816 (Classe II: máquinas médias 15–75 kW)
#   Temperatura — limite típico de carcaça para classe F (155°C máximo)
# ---------------------------------------------------------------------------
_LIMITES: dict[str, dict] = {
    "Temperatura (°C)": {"aviso": 75,  "critico": 90},   # °C
    "Vibração (mm/s)":  {"aviso": 4.5, "critico": 7.1},  # mm/s — ISO 10816 Classe II
}


# Constante exportada: define as colunas do gr.Dataframe do histórico
COLUNAS_HISTORICO = ["Timestamp", "Tensão (V)", "Corrente (A)", "Temp (°C)", "Vibração (mm/s)", "RPM"]


def _classificar_severidade(grandeza: str, valor: float) -> str:
    """
    Retorna o nível de severidade de uma leitura: 'normal', 'aviso' ou 'critico'.

    Compara o valor com os limites definidos em _LIMITES.
    Grandezas sem limite registrado sempre retornam 'normal'.
    """
    limites = _LIMITES.get(grandeza)
    if not limites:
        return "normal"

    if valor >= limites["critico"]:
        return "critico"
    if valor >= limites["aviso"]:
        return "aviso"
    return "normal"


def leitura_como_markdown(tag: str) -> str:
    """
    Retorna a leitura atual do equipamento formatada como Markdown.

    A tabela Markdown inclui uma coluna de ícone de severidade para que o
    operador identifique anomalias de forma imediata (design para latência).

    Retorna string Markdown pronta para gr.Markdown.
    """
    # Busca o status atual para usar o perfil de simulação correto
    eq = eq_provider.buscar_por_tag(tag)
    status = eq["status"] if eq else "Operacional"

    # Obtém leitura bruta e converte para unidades físicas
    leitura_bruta = sensor_provider.leitura_atual(tag, status)
    grandezas = sensor_provider.converter_para_unidades(leitura_bruta)

    # Mapeamento de severidade para ícone visual (cores semânticas)
    icone_sev = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}

    # Cabeçalho com identificação do equipamento e timestamp
    md = f"## 📡 Leitura — {tag}\n"
    md += f"**Timestamp:** `{leitura_bruta['timestamp']}`\n\n"

    # Tabela de grandezas com valor, unidade e ícone de severidade
    md += "| Grandeza | Valor | Unidade | Status |\n"
    md += "|---|---|---|---|\n"

    for nome, dados in grandezas.items():
        sev   = _classificar_severidade(nome, dados["valor"])
        icone = icone_sev[sev]
        md += f"| {nome} | **{dados['valor']}** | {dados['unidade']} | {icone} |\n"

    return md


def historico_para_tabela(tag: str) -> list[list]:
    """
    Retorna o histórico de 48 leituras (últimas 24h) como lista de listas.

    O gr.Dataframe espera lista de listas, com os valores na mesma ordem
    que as colunas definidas em COLUNAS_HISTORICO.
    """
    eq = eq_provider.buscar_por_tag(tag)
    status = eq["status"] if eq else "Operacional"

    # Solicita o histórico simulado ao provider
    historico = sensor_provider.historico_simulado(tag, status)

    # Transforma cada leitura em uma linha da tabela
    return [
        [
            h["timestamp"],
            h["tensao_v"],
            h["corrente_a"],
            h["temp_c"],
            h["vibracao_mms"],
            h["rotacao_rpm"],
        ]
        for h in historico
    ]
