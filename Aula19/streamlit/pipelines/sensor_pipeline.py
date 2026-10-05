# =============================================================================
# pipelines/sensor_pipeline.py — Apresentação dos dados de sensores
#
# A classificação de severidade NÃO está aqui: ela é regra de negócio e vive
# em backend/routers/sensores.py. Este arquivo recebe severidade_temp e
# severidade_vibracao já calculadas e decide apenas como exibi-las.
# =============================================================================

import pandas as pd

import providers.api_provider as api_provider

COLUNAS_HISTORICO = [
    "Timestamp", "Tensão (V)", "Corrente (A)",
    "Temp (°C)", "Vibração (mm/s)", "RPM",
]

ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def leitura_para_cards(tag: str) -> dict | None:
    """
    Devolve a leitura atual em um formato pronto para st.metric.

    Cada item é (rótulo, valor formatado, ícone de severidade). Devolve None
    quando a API não respondeu — a página mostra o aviso apropriado.
    """
    leitura = api_provider.leitura_atual(tag)
    if not leitura or not leitura.get("timestamp"):
        return None

    return {
        "timestamp": leitura["timestamp"],
        "metricas": [
            ("Tensão", f"{leitura['tensao_v']} V", "🟢"),
            ("Corrente", f"{leitura['corrente_a']} A", "🟢"),
            ("Temperatura", f"{leitura['temp_c']} °C", ICONE_SEV[leitura["severidade_temp"]]),
            ("Vibração", f"{leitura['vibracao_mms']} mm/s", ICONE_SEV[leitura["severidade_vibracao"]]),
            ("Rotação", f"{leitura['rotacao_rpm']} RPM", "🟢"),
        ],
    }


def historico_para_tabela(tag: str) -> pd.DataFrame:
    """Devolve o histórico de leituras como DataFrame, na ordem de COLUNAS_HISTORICO."""
    historico = api_provider.historico_simulado(tag)

    linhas = [
        [h["timestamp"], h["tensao_v"], h["corrente_a"],
         h["temp_c"], h["vibracao_mms"], h["rotacao_rpm"]]
        for h in historico
    ]
    return pd.DataFrame(linhas, columns=COLUNAS_HISTORICO)
