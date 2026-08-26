# =============================================================================
# routers/plantas.py — Endpoints de /v1/plantas
# =============================================================================

from fastapi import APIRouter, Security

from auth.seguranca import verificar_chave
from models.saida import LocalizacaoSaida
import providers.planta_provider as planta_provider

router = APIRouter(prefix="/plantas", tags=["Plantas"])


@router.get("", response_model=list[str])
def listar_plantas(_: str = Security(verificar_chave)):
    return planta_provider.listar_plantas()


@router.get("/{planta}/areas", response_model=list[str])
def listar_areas(planta: str, _: str = Security(verificar_chave)):
    return planta_provider.listar_areas(planta)


@router.get("/{planta}/areas/{area}/equipamentos", response_model=list[str])
def listar_equipamentos_area(planta: str, area: str, _: str = Security(verificar_chave)):
    return planta_provider.listar_equipamentos(planta, area)


@router.get("/localizacao/{tag}", response_model=LocalizacaoSaida)
def buscar_localizacao(tag: str, _: str = Security(verificar_chave)):
    planta, area = planta_provider.buscar_localizacao(tag)
    return {"planta": planta, "area": area}
