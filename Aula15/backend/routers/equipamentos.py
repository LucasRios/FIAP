# =============================================================================
# routers/equipamentos.py — Endpoints de /v1/equipamentos
# =============================================================================

from fastapi import APIRouter, HTTPException, Security

from auth.seguranca import verificar_chave
from models.entrada import EquipamentoEntrada
from models.saida import EquipamentoSaida, MensagemSaida
import providers.equipamento_provider as eq_provider

router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])


@router.get("", response_model=list[EquipamentoSaida])
def listar_equipamentos(_: str = Security(verificar_chave)):
    """Lista todos os motores cadastrados."""
    return eq_provider.listar_todos()


@router.get("/tags", response_model=list[str])
def listar_tags(_: str = Security(verificar_chave)):
    """Lista só as TAGs — usado para popular dropdowns no front-end."""
    return eq_provider.tags_disponiveis()


@router.get("/{tag}", response_model=EquipamentoSaida)
def buscar_equipamento(tag: str, _: str = Security(verificar_chave)):
    eq = eq_provider.buscar_por_tag(tag)
    if not eq:
        raise HTTPException(status_code=404, detail=f"Equipamento {tag} não encontrado.")
    return eq


@router.post("", response_model=MensagemSaida, status_code=201)
def salvar_equipamento(entrada: EquipamentoEntrada, _: str = Security(verificar_chave)):
    """Cria ou atualiza um equipamento (upsert pela TAG)."""
    sucesso, mensagem = eq_provider.salvar(entrada.model_dump())
    if not sucesso:
        raise HTTPException(status_code=400, detail=mensagem)
    return {"mensagem": mensagem}
