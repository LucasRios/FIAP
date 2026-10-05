from fastapi import APIRouter, HTTPException, Security, status,Header
from typing import Optional 


from auth.seguranca import verificar_chave
from models.entrada import EquipamentoEntrada
from models.saida import EquipamentoSaida, MensagemSaida
import providers.equipamento_provider as eq_provider

from langsmith import trace


router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])


@router.get("/", response_model=list[EquipamentoSaida])
def listar_equipamentos(
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
):
    with trace (
        name="endpoint_listar_equipamntos",
        run_type="chain",
        tags=["forzy", "equipamentos", "endpoint"],
        metadata={
            "session_id": x_session_id,
            "feature": x_feature
        } 
    ):
        return eq_provider.listar_todos()

 
@router.get("/tags", response_model=list[str])
def listar_tags(_:str = Security(verificar_chave)):
    return eq_provider.tags_disponiveis()

 
@router.get("/{tag}", response_model=EquipamentoSaida)
def buscar_equipamento(tag: str, _:str = Security(verificar_chave)):
    eq = eq_provider.buscar_por_tag(tag)
    if not eq:
        raise HTTPException( status_code= status.HTTP_404_NOT_FOUND, detail=f"a tag {tag} não foi encontrada" )

    return eq

@router.post("/", response_model=MensagemSaida, status_code=201)
def salvar_equipamento(entrada: EquipamentoEntrada, _:str = Security(verificar_chave)):
    sucesso, mensagem = eq_provider.salvar(entrada.model_dump())

    if not sucesso:
        raise HTTPException(status_code=400, detail= mensagem)

    return {"mensagem":mensagem}