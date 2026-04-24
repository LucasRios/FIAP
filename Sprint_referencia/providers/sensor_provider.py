# =============================================================================
# providers/sensor_provider.py — Fonte de dados dos sensores IoT
#
# Simulação vs. Produção:
# -----------------------
# Aqui simulamos leituras de sensores com ruído gaussiano realista.
# Os perfis de operação (_PERFIS) definem distribuições diferentes
# dependendo do status do motor (ligado, em manutenção, desligado).
#
# Para produção, substitua as funções por chamadas a:
#   - Broker MQTT (ex: Mosquitto, HiveMQ) para leituras em tempo real
#   - InfluxDB / TimescaleDB para séries temporais históricas
#   - API REST de um gateway IoT
#
# Grandezas físicas simuladas:
#   - Tensão de linha fase-fase (V)
#   - Corrente de fase RMS (A)
#   - Temperatura de carcaça (°C)
#   - Vibração RMS (mm/s) — conforme ISO 10816
#   - Velocidade de rotação real (RPM)
# =============================================================================

import random
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# _PERFIS — distribuições de simulação por status operacional
#
# Cada perfil define (valor_base, desvio_padrão) para cada grandeza.
# O ruído gaussiano faz os valores oscilarem de forma realista.
# ---------------------------------------------------------------------------
_PERFIS: dict[str, dict] = {
    "Operacional": {
        # Motor em plena carga: tensão estável, corrente próxima da nominal
        "tensao":    (380, 8),    # V   — oscilação normal de rede
        "corrente":  (40,  3),    # A   — variação por carga
        "temp":      (62,  4),    # °C  — aquecimento em regime
        "vibracao":  (2.1, 0.4),  # mm/s — vibração normal de operação
        "rpm":       (1760, 15),  # RPM — escorregamento do motor
    },
    "Em Manutenção": {
        # Motor desligado para manutenção: sem corrente, temperatura ambiente
        "tensao":    (0,  0),
        "corrente":  (0,  0),
        "temp":      (28, 2),
        "vibracao":  (0,  0),
        "rpm":       (0,  0),
    },
    "Desligado": {
        # Motor com tensão presente mas parado: sem corrente nem rotação
        "tensao":    (380, 2),
        "corrente":  (0,   0),
        "temp":      (30,  2),
        "vibracao":  (0.1, 0.05),  # vibração residual da estrutura
        "rpm":       (0,   0),
    },
}


def _aplicar_ruido(base: float, sigma: float) -> float:
    """
    Gera um valor com distribuição gaussiana em torno da base.
    Garante que o resultado seja sempre >= 0 (grandezas físicas não negativas).
    """
    return round(max(0.0, base + random.gauss(0, sigma)), 2)


def leitura_atual(tag: str, status: str = "Operacional") -> dict:
    """
    Retorna uma leitura instantânea simulada dos sensores.

    Parâmetros:
        tag:    TAG do equipamento — incluído na leitura para rastreabilidade
        status: estado operacional atual — determina qual perfil de simulação usar

    Retorna dicionário com todas as grandezas físicas e o timestamp da leitura.
    """
    # Seleciona o perfil de acordo com o status; fallback para Operacional
    perfil = _PERFIS.get(status, _PERFIS["Operacional"])

    return {
        "tag":          tag,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tensao_v":     _aplicar_ruido(*perfil["tensao"]),
        "corrente_a":   _aplicar_ruido(*perfil["corrente"]),
        "temp_c":       _aplicar_ruido(*perfil["temp"]),
        "vibracao_mms": _aplicar_ruido(*perfil["vibracao"]),
        "rotacao_rpm":  _aplicar_ruido(*perfil["rpm"]),
    }


def historico_simulado(tag: str, status: str = "Operacional", n_pontos: int = 48) -> list[dict]:
    """
    Gera um histórico simulado das últimas 24 horas com intervalo de 30 minutos.

    48 pontos × 30 min = 24 horas de histórico.

    Em produção: substitua por uma query à série temporal (InfluxDB, etc.).
    """
    agora = datetime.now()

    # Gera cada ponto no passado, do mais antigo para o mais recente
    historico = []
    for i in range(n_pontos, 0, -1):
        leitura = leitura_atual(tag, status)

        # Sobrescreve o timestamp com o momento correto no passado
        ts = agora - timedelta(minutes=30 * i)
        leitura["timestamp"] = ts.strftime("%Y-%m-%d %H:%M")

        historico.append(leitura)

    return historico


def converter_para_unidades(leitura: dict) -> dict:
    """
    Transforma o dicionário de leitura bruta em um mapa estruturado com
    valor, unidade de engenharia e descrição de cada grandeza.

    Em produção: aplique aqui os fatores de escala reais dos sensores ADC
    (ex: counts × fator_escala + offset → valor em engenharia).

    Retorna dicionário onde cada chave é o nome da grandeza para exibição.
    """
    return {
        "Tensão (V)":        {"valor": leitura["tensao_v"],     "unidade": "V",    "desc": "Tensão de linha fase-fase"},
        "Corrente (A)":      {"valor": leitura["corrente_a"],   "unidade": "A",    "desc": "Corrente de fase (eficaz)"},
        "Temperatura (°C)":  {"valor": leitura["temp_c"],       "unidade": "°C",   "desc": "Temperatura de carcaça"},
        "Vibração (mm/s)":   {"valor": leitura["vibracao_mms"], "unidade": "mm/s", "desc": "Vibração RMS — ISO 10816"},
        "Rotação (RPM)":     {"valor": leitura["rotacao_rpm"],  "unidade": "RPM",  "desc": "Velocidade de rotação real"},
    }
