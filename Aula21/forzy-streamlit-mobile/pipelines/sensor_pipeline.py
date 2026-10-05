# =============================================================================
# pipelines/sensor_pipeline.py — Leituras de sensores prontas para a tela
#
# A severidade (normal | aviso | critico) vem calculada do back-end. Esta
# pipeline só organiza os dados; a escolha de cor, ícone e forma de cada
# severidade pertence ao design system (ui/tokens.py), não a ela.
# =============================================================================

import pandas as pd

import providers.api_provider as api_provider
from pipelines.formatacao import GRANDEZAS, com_unidade, hora

COLUNAS_HISTORICO = ["Hora", "Tensão (V)", "Corrente (A)", "Temp (°C)", "Vibração (mm/s)", "RPM"]


def grandezas_atuais(tag: str) -> dict | None:
    """
    Leitura atual + série das últimas 24 h de cada grandeza, num só pacote.

    Devolve None quando a API não respondeu. A série alimenta a sparkline do
    card: tendência visível sem um gráfico inteiro ocupando a tela.
    """
    leitura = api_provider.leitura_atual(tag)
    if not leitura or not leitura.get("timestamp"):
        return None
    historico = api_provider.historico_simulado(tag)

    itens = []
    for chave, g in GRANDEZAS.items():
        itens.append({
            "chave": chave,
            "nome": g["nome"],
            "valor": com_unidade(chave, leitura[chave]),
            "severidade": leitura[g["chave_sev"]] if g["chave_sev"] else None,
            "serie": [h[chave] for h in historico],
        })
    return {"hora": hora(leitura["timestamp"]), "itens": itens}


def historico_para_tabela(tag: str) -> pd.DataFrame:
    """Histórico como DataFrame, para consulta detalhada e download em CSV."""
    linhas = [
        [hora(h["timestamp"]), h["tensao_v"], h["corrente_a"], h["temp_c"], h["vibracao_mms"], h["rotacao_rpm"]]
        for h in api_provider.historico_simulado(tag)
    ]
    return pd.DataFrame(linhas, columns=COLUNAS_HISTORICO)
