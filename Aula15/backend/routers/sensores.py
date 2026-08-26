# =============================================================================
# routers/sensores.py — Endpoints de /v1/sensores
#
# A classificação de severidade (ISO 10816 para vibração, limites típicos
# de carcaça classe F para temperatura) é regra de negócio — por isso vive
# aqui, e não no front-end. Antes ela estava duplicada em dois pipelines
# do Gradio (sensor_pipeline.py e dashboard_pipeline.py); agora existe em
# um único lugar.
# =============================================================================

from fastapi import APIRouter, Security

from auth.seguranca import verificar_chave
from models.saida import LeituraSaida
import providers.sensor_provider as sensor_provider

router = APIRouter(prefix="/sensores", tags=["Sensores"])

_LIMITES = {
    "temp_c":       {"aviso": 75,  "critico": 90},
    "vibracao_mms": {"aviso": 4.5, "critico": 7.1},
}


def _severidade(chave: str, valor: float) -> str:
    limites = _LIMITES.get(chave)
    if not limites:
        return "normal"
    if valor >= limites["critico"]:
        return "critico"
    if valor >= limites["aviso"]:
        return "aviso"
    return "normal"


def _com_severidade(leitura: dict) -> dict:
    return {
        **leitura,
        "severidade_temp":     _severidade("temp_c", leitura["temp_c"]),
        "severidade_vibracao": _severidade("vibracao_mms", leitura["vibracao_mms"]),
    }


@router.get("/{tag}/leitura-atual", response_model=LeituraSaida)
def leitura_atual(tag: str, _: str = Security(verificar_chave)):
    leitura = sensor_provider.leitura_atual(tag)
    return _com_severidade(leitura)


@router.get("/{tag}/historico", response_model=list[LeituraSaida])
def historico(tag: str, n: int = 48, _: str = Security(verificar_chave)):
    pontos = sensor_provider.historico_simulado(tag, n_pontos=n)
    return [_com_severidade(p) for p in pontos]
