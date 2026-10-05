import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
APP_VERSION = os.getenv("APP_VERSION")

_HEADERS = {"X-API-Key": API_KEY}

_SESSION_ID = str(uuid.uuid4())  
_TIMEOUT = 10


def _headers(feature: str) -> dict:
    return {
        "X-API-Key": API_KEY,
        "X-Session-Id": _SESSION_ID,
        "X-App-Version": APP_VERSION,
        "X-Feature": feature
    }

def _post(path:str, corpo: dict ) -> tuple[bool,str]:
    try:
        r = requests.post(f"{API_URL}{path}" , headers=_HEADERS, json=corpo, timeout=_TIMEOUT)
        r.raise_for_status()
        return True, r.json().get("mensagem","operação realizada com sucesso")
    except requests.ConnectionError:
        print("não chegou lá a comunicação")
        return False, "não chegou lá"
    except requests.Timeout:
        print("deu timeout")
        return False, "deu timeout"
    except requests.HTTPError as e:
        print (f"{e.response.status_code} - {e.response.text}")
        return False, f"{e.response.status_code} - {e.response.text}"
    
def _get(path: str, feature:str, params: dict | None = None):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_headers(feature), params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        print(f"[api_provider] Não foi possível conectar ao back-end em {API_URL}.")
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        print(f"[api_provider] Erro {e.response.status_code} em {path}: {e.response.text}")
        return None

 

def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos",  feature="equipamentos") or []


def tags_disponiveis() -> list[str]:
    return _get("/v1/equipamentos/tags", feature="equipamentos") or []


def buscar_por_tag(tag: str) -> dict | None:
    return _get(f"/v1/equipamentos/{tag}", feature="equipamentos")

def salvar(dados: dict) -> tuple[bool, str]:
    return _post("/v1/equipamentos", dados)

# ---------------------------------------------------------------------------
# Plantas — mesma interface pública de planta_provider.py
# ---------------------------------------------------------------------------

def listar_plantas() -> list[str]:
    return _get("/v1/plantas", feature="plantas") or []


def listar_areas(planta: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas", feature="plantas") or []


def listar_equipamentos(planta: str, area: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos", feature="plantas") or []


def buscar_localizacao(tag: str) -> tuple[str, str]:
    loc = _get(f"/v1/plantas/localizacao/{tag}", feature="plantas")
    if not loc:
        return "", ""
    return loc["planta"], loc["area"]


# ---------------------------------------------------------------------------
# Sensores — mesma interface pública de sensor_provider.py
# (a severidade agora vem pronta do back-end, dentro do dicionário)
# ---------------------------------------------------------------------------

def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual", feature="sensores") or {
        "tag": tag, "timestamp": "", "tensao_v": 0, "corrente_a": 0,
        "temp_c": 0, "vibracao_mms": 0, "rotacao_rpm": 0, "falha": 0,
        "severidade_temp": "normal", "severidade_vibracao": "normal",
    }


def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    return _get(f"/v1/sensores/{tag}/historico", params={"n": n_pontos}, feature="sensores") or []
