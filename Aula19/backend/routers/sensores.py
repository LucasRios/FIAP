# backend/routers/sensores.py
from fastapi import APIRouter, Security, Header
from typing import Optional 

from auth.seguranca import verificar_chave
from models.saida import LeituraSaida
import providers.sensor_provider as sensor_provider

from langsmith import traceable, trace

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

@traceable(name="classificar_severidade", run_type="tool", tags=["forzy", "sensores"])
def _com_severidade(leitura: dict) -> dict:
    return {
        **leitura,
        "severidade_temp":     _severidade("temp_c", leitura["temp_c"]),
        "severidade_vibracao": _severidade("vibracao_mms", leitura["vibracao_mms"]),
    }


@router.get("/{tag}/leitura-atual", response_model=LeituraSaida)
def leitura_atual(
    tag: str,
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_app_version: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
    x_client_plataform: Optional[str] = Header(None),
):
    with trace(
        name="endpoint_leitura_atual",
        run_type="chain",
        tags=["forzy", "sensores", "endpoint"],
        metadata={
            "tag_filtrada": tag,
            "session_id": x_session_id,
            "app_version": x_app_version,
            "feature": x_feature,
            "client_plataform": x_client_plataform,
        }
    ):
        leitura = sensor_provider.leitura_atual(tag)   
        return _com_severidade(leitura)                


@router.get("/{tag}/historico", response_model=list[LeituraSaida])
def historico(tag: str, n: int = 48, _: str = Security(verificar_chave)):
    pontos = sensor_provider.historico_simulado(tag, n_pontos=n)
    return [_com_severidade(p) for p in pontos]