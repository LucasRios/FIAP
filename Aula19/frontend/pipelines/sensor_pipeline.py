# =============================================================================
# pipelines/sensor_pipeline.py — Lógica de apresentação dos dados de sensores
#
# A classificação de severidade (antes feita aqui com _classificar_severidade
# e o dicionário _LIMITES) SAIU deste arquivo — ela agora vive em
# backend/routers/sensores.py, porque é regra de negócio, não apresentação.
# Este pipeline só formata o que já vem pronto da API.
# =============================================================================

import providers.api_provider as api_provider

# Constante exportada: define as colunas do gr.Dataframe do histórico
COLUNAS_HISTORICO = ["Timestamp", "Tensão (V)", "Corrente (A)", "Temp (°C)", "Vibração (mm/s)", "RPM"]

_ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def leitura_como_markdown(tag: str) -> str:
    """
    Retorna a leitura atual do equipamento formatada como Markdown.

    A severidade de cada grandeza já vem calculada pelo back-end
    (campos severidade_temp / severidade_vibracao) — este pipeline
    só decide como exibir, não decide o que é normal/aviso/crítico.
    """
    leitura = api_provider.leitura_atual(tag)
    if not leitura or not leitura.get("timestamp"):
        return f"_Não foi possível obter a leitura de **{tag}**._"

    md  = f"## 📡 Leitura — {tag}\n"
    md += f"**Timestamp:** `{leitura['timestamp']}`\n\n"
    md += "| Grandeza | Valor | Unidade | Status |\n"
    md += "|---|---|---|---|\n"
    md += f"| Tensão (V) | **{leitura['tensao_v']}** | V | 🟢 |\n"
    md += f"| Corrente (A) | **{leitura['corrente_a']}** | A | 🟢 |\n"
    md += f"| Temperatura (°C) | **{leitura['temp_c']}** | °C | {_ICONE_SEV[leitura['severidade_temp']]} |\n"
    md += f"| Vibração (mm/s) | **{leitura['vibracao_mms']}** | mm/s | {_ICONE_SEV[leitura['severidade_vibracao']]} |\n"
    md += f"| Rotação (RPM) | **{leitura['rotacao_rpm']}** | RPM | 🟢 |\n"
    return md


def historico_para_tabela(tag: str) -> list[list]:
    """
    Retorna o histórico de leituras como lista de listas, pronto para
    o gr.Dataframe. Os dados já chegam prontos do back-end — aqui só
    reorganizamos em linhas na ordem de COLUNAS_HISTORICO.
    """
    historico = api_provider.historico_simulado(tag)
    return [
        [h["timestamp"], h["tensao_v"], h["corrente_a"], h["temp_c"], h["vibracao_mms"], h["rotacao_rpm"]]
        for h in historico
    ]
