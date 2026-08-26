# =============================================================================
# models/entrada.py — Modelos Pydantic de REQUEST (o que o cliente envia)
# =============================================================================

from pydantic import BaseModel, Field


class EquipamentoEntrada(BaseModel):
    tag: str                  = Field(..., examples=["MTR-004"])
    modelo: str
    fabricante: str
    potencia_cv: float        = 0
    tensao_v: int              = 380
    corrente_nominal_a: float = 0
    rotacao_rpm: int           = 0
    fator_potencia: float     = 0.86
    classe_isolamento: str    = "F"
    ip: str                    = "IP55"
    peso_kg: float             = 0
    local: str                 = ""
    status: str                 = "Operacional"
