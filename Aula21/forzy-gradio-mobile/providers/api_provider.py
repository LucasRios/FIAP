# =============================================================================
# providers/api_provider.py — Única porta de saída do front Gradio para a API
#
# Expõe as mesmas funções da versão Streamlit; por isso as pipelines são
# copiadas sem alterar uma linha. Diferenças em relação ao Streamlit:
#
#   - não existe st.cache_data: um cache com tempo de validade simples,
#     escrito aqui, evita refazer a mesma chamada várias vezes por tela;
#   - o servidor Gradio atende TODOS os usuários no mesmo processo, então
#     nada aqui guarda estado de um usuário em variável de módulo.
# =============================================================================

import functools
import os
import threading
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv()

# .strip(): o --env-file do docker run preserva espaço no fim da linha do .env.
API_URL = os.getenv("API_URL", "http://localhost:8000").strip().rstrip("/")
API_KEY = os.getenv("API_KEY", "chave-local-dev").strip()
APP_VERSION = os.getenv("APP_VERSION", "2.0.0-gradio").strip()

_TIMEOUT = 15
_TIMEOUT_ACORDAR = 75
_ID_PROCESSO = str(uuid.uuid4())  # Gradio: um processo atende todas as sessões


def _headers(feature: str) -> dict:
    return {
        "X-API-Key": API_KEY,
        "X-Session-Id": _ID_PROCESSO,
        "X-App-Version": APP_VERSION,
        "X-Feature": feature,
        "X-Client-Platform": "gradio-mobile",
    }


# ---------------------------------------------------------------------------
# Cache com validade — o equivalente mínimo ao @st.cache_data
# ---------------------------------------------------------------------------
_cache: dict = {}
_trava = threading.Lock()


def _cache_ttl(segundos: int):
    """Memoriza o resultado por `segundos`. Só para leituras, nunca para escritas."""
    def decorador(funcao):
        @functools.wraps(funcao)
        def envolvida(*args):
            chave = (funcao.__name__, args)
            agora = time.monotonic()
            with _trava:
                if chave in _cache and agora - _cache[chave][0] < segundos:
                    return _cache[chave][1]
            resultado = funcao(*args)
            if resultado:  # falhas não são memorizadas: a próxima tentativa vai à rede
                with _trava:
                    _cache[chave] = (agora, resultado)
            return resultado
        return envolvida
    return decorador


def limpar_cache() -> None:
    """Descarta respostas memorizadas — chamada depois de toda escrita."""
    with _trava:
        _cache.clear()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _get(path: str, feature: str, params: dict | None = None):
    """GET autenticado. Devolve None em qualquer falha; a tela trata o None."""
    try:
        r = requests.get(f"{API_URL}{path}", headers=_headers(feature), params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        if e.response.status_code != 404:
            print(f"[api_provider] {e.response.status_code} em {path}")
        return None
    except requests.RequestException as e:
        print(f"[api_provider] falha de rede em {path}: {type(e).__name__}")
        return None


def _post(path: str, corpo: dict) -> tuple[bool, str]:
    try:
        r = requests.post(f"{API_URL}{path}", headers=_headers("cadastro"), json=corpo, timeout=_TIMEOUT)
        r.raise_for_status()
        return True, r.json().get("mensagem", "Operação realizada com sucesso.")
    except requests.HTTPError as e:
        try:
            detalhe = e.response.json().get("detail", e.response.text)
        except ValueError:
            detalhe = e.response.text
        return False, f"{e.response.status_code} — {detalhe}"
    except requests.RequestException:
        return False, f"Não foi possível conectar à API em {API_URL}."


_acordada = False


def acordar_api() -> bool:
    """Tira a API da hibernação do plano gratuito. Chamada uma vez, antes do launch()."""
    global _acordada
    if _acordada:
        return True
    try:
        requests.get(f"{API_URL}/", timeout=_TIMEOUT_ACORDAR)
        _acordada = True
    except requests.RequestException:
        print(f"[api_provider] a API em {API_URL} não respondeu ao despertar.")
    return _acordada


# ---------------------------------------------------------------------------
# Equipamentos
# ---------------------------------------------------------------------------
@_cache_ttl(120)
def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos", "equipamentos") or []


@_cache_ttl(120)
def tags_disponiveis() -> list[str]:
    return _get("/v1/equipamentos/tags", "equipamentos") or []


@_cache_ttl(60)
def buscar_por_tag(tag: str) -> dict | None:
    return _get(f"/v1/equipamentos/{tag}", "equipamentos")


def salvar(dados: dict) -> tuple[bool, str]:
    return _post("/v1/equipamentos", dados)


# ---------------------------------------------------------------------------
# Plantas
# ---------------------------------------------------------------------------
@_cache_ttl(600)
def listar_plantas() -> list[str]:
    return _get("/v1/plantas", "plantas") or []


@_cache_ttl(600)
def listar_areas(planta: str) -> list[str]:
    return (_get(f"/v1/plantas/{planta}/areas", "plantas") or []) if planta else []


@_cache_ttl(600)
def listar_equipamentos(planta: str, area: str) -> list[str]:
    if not planta or not area:
        return []
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos", "plantas") or []


# ---------------------------------------------------------------------------
# Sensores — validade curta: telemetria envelhece rápido
# ---------------------------------------------------------------------------
@_cache_ttl(20)
def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual", "sensores") or {}


@_cache_ttl(20)
def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    return _get(f"/v1/sensores/{tag}/historico", "sensores", params={"n": n_pontos}) or []
