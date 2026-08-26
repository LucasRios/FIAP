# =============================================================================
# providers/api_provider.py — Camada de acesso a dados via HTTP
#
# Substitui equipamento_provider.py, sensor_provider.py e planta_provider.py
# do Sprint anterior. Expõe as MESMAS funções que eles expunham — só que por
# trás, em vez de acessar SQLite/dict direto, faz uma chamada HTTP autenticada
# para o back-end FastAPI.
#
# Por isso as pipelines quase não precisam mudar: só o import.
# =============================================================================

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "chave-local-dev")

_HEADERS = {"X-API-Key": API_KEY}
_TIMEOUT = 10


def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_HEADERS, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        print(f"[api_provider] Não foi possível conectar ao back-end em {API_URL}.")
        return None
    except requests.Timeout:
        print(f"[api_provider] Tempo esgotado ao chamar {path}.")
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        print(f"[api_provider] Erro {e.response.status_code} em {path}: {e.response.text}")
        return None


def _post(path: str, corpo: dict) -> tuple[bool, str]:
    try:
        r = requests.post(f"{API_URL}{path}", json=corpo, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        return True, r.json().get("mensagem", "Operação realizada com sucesso.")
    except requests.ConnectionError:
        return False, f"Não foi possível conectar ao back-end em {API_URL}."
    except requests.Timeout:
        return False, "A requisição demorou mais que o esperado. Tente novamente."
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except ValueError:
            detail = str(e)
        return False, detail


# ---------------------------------------------------------------------------
# Equipamentos — mesma interface pública de equipamento_provider.py
# ---------------------------------------------------------------------------

def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos") or []


def tags_disponiveis() -> list[str]:
    return _get("/v1/equipamentos/tags") or []


def buscar_por_tag(tag: str) -> dict | None:
    return _get(f"/v1/equipamentos/{tag}")


def salvar(dados: dict) -> tuple[bool, str]:
    return _post("/v1/equipamentos", dados)


# ---------------------------------------------------------------------------
# Plantas — mesma interface pública de planta_provider.py
# ---------------------------------------------------------------------------

def listar_plantas() -> list[str]:
    return _get("/v1/plantas") or []


def listar_areas(planta: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas") or []


def listar_equipamentos(planta: str, area: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos") or []


def buscar_localizacao(tag: str) -> tuple[str, str]:
    loc = _get(f"/v1/plantas/localizacao/{tag}")
    if not loc:
        return "", ""
    return loc["planta"], loc["area"]


# ---------------------------------------------------------------------------
# Sensores — mesma interface pública de sensor_provider.py
# (a severidade agora vem pronta do back-end, dentro do dicionário)
# ---------------------------------------------------------------------------

def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual") or {
        "tag": tag, "timestamp": "", "tensao_v": 0, "corrente_a": 0,
        "temp_c": 0, "vibracao_mms": 0, "rotacao_rpm": 0, "falha": 0,
        "severidade_temp": "normal", "severidade_vibracao": "normal",
    }


def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    return _get(f"/v1/sensores/{tag}/historico", params={"n": n_pontos}) or []
