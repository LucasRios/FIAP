from pydantic import BaseModel, Field

class EquipamentoSaida(BaseModel):
    tag: str
    modelo: str
    fabricante: str
    potencia_cv: float
    tensao_v: int
    corrente_nominal_a: float
    rotacao_rpm: int
    fator_potencia: float
    classe_isolamento: str
    ip: str
    peso_kg: float
    local: str
    status: str
    cadastrado_em: str


class LocalizacaoSaida(BaseModel):
    planta:str
    area:str

class LeituraSaida(BaseModel):
    tag: str
    timestamp: str
    tensao_v: float
    corrente_a: float
    temp_c: float
    vibracao_mms: float
    rotacao_rpm: float
    falha: int
    severidade_temp:str
    severidade_vibracao:str

class MensagemSaida(BaseModel):
    mensagem:str