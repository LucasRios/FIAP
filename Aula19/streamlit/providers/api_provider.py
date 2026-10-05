# =============================================================================
# providers/api_provider.py — Única porta de saída do front-end para o back-end
#
# Expõe as MESMAS funções da versão Gradio. O que muda aqui:
#   1. As configurações vêm de st.secrets (nuvem) ou do .env (local)
#   2. As leituras são memorizadas com @st.cache_data — sem isso, cada rerun
#      do Streamlit refaria todas as chamadas HTTP da tela
#   3. O header X-Client-Platform identifica este cliente no LangSmith
#
# Nenhuma função desta camada conhece Streamlit além do cache: quem desenha
# a tela são as features; quem formata são as pipelines.
# =============================================================================

import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # local: lê o .env. Na nuvem o arquivo não existe e nada acontece.


def _config(chave: str, padrao: str = "") -> str:
    """
    Busca uma configuração em duas fontes, nesta ordem:
      1. st.secrets  — usado no Streamlit Community Cloud
      2. os.environ  — usado localmente (via .env) e no Docker

    Acessar st.secrets sem o arquivo secrets.toml levanta exceção,
    por isso a leitura fica protegida.
    """
    try:
        if chave in st.secrets:
            return str(st.secrets[chave])
    except Exception:
        pass
    return os.getenv(chave, padrao)


# .strip() protege contra espaço ou tabulação no fim da linha do .env: o
# python-dotenv remove, mas o --env-file do docker run preserva, e um espaço
# invisível na API_KEY vira um 401 que só aparece dentro do container.
# rstrip("/") evita que uma barra no fim da URL gere caminhos como //v1/plantas.
API_URL = _config("API_URL", "http://localhost:8000").strip().rstrip("/")
API_KEY = _config("API_KEY", "chave-local-dev").strip()
APP_VERSION = _config("APP_VERSION", "2.0.0-streamlit").strip()

_TIMEOUT = 15          # chamadas normais, com o serviço já de pé
_TIMEOUT_ACORDAR = 75  # primeira chamada: a plataforma pode estar hibernada


def _session_id() -> str:
    """
    Identificador da sessão do usuário, enviado no header X-Session-Id.

    Na versão Gradio era um UUID por PROCESSO. No Streamlit cada aba do
    navegador tem o seu próprio st.session_state, então conseguimos um
    identificador por USUÁRIO — mais útil para investigar um relato
    individual no LangSmith.
    """
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())
    return st.session_state["_session_id"]


def _headers(feature: str) -> dict:
    return {
        "X-API-Key": API_KEY,
        "X-Session-Id": _session_id(),
        "X-App-Version": APP_VERSION,
        "X-Feature": feature,
        "X-Client-Platform": "streamlit-cloud",
    }


def _get(path: str, feature: str, params: dict | None = None):
    """GET autenticado. Devolve None em qualquer falha — a UI trata o None."""
    try:
        r = requests.get(
            f"{API_URL}{path}", headers=_headers(feature), params=params, timeout=_TIMEOUT
        )
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.session_state["_ultimo_erro"] = f"Não foi possível conectar à API em {API_URL}."
        return None
    except requests.Timeout:
        st.session_state["_ultimo_erro"] = "A API demorou demais para responder."
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        if e.response.status_code == 401:
            st.session_state["_ultimo_erro"] = "Chave de API inválida (401)."
        else:
            st.session_state["_ultimo_erro"] = f"Erro {e.response.status_code} em {path}."
        return None


def _post(path: str, corpo: dict) -> tuple[bool, str]:
    """POST autenticado. Devolve (sucesso, mensagem) para a UI exibir."""
    try:
        r = requests.post(
            f"{API_URL}{path}", headers=_headers("cadastro"), json=corpo, timeout=_TIMEOUT
        )
        r.raise_for_status()
        return True, r.json().get("mensagem", "Operação realizada com sucesso.")
    except requests.ConnectionError:
        return False, f"Não foi possível conectar à API em {API_URL}."
    except requests.Timeout:
        return False, "A API demorou demais para responder."
    except requests.HTTPError as e:
        try:
            detalhe = e.response.json().get("detail", e.response.text)
        except ValueError:
            detalhe = e.response.text
        return False, f"{e.response.status_code} — {detalhe}"


def acordar_api() -> bool:
    """
    Tira a API da hibernação antes da primeira tela.

    Plataformas gratuitas pausam o serviço depois de alguns minutos sem acesso.
    A primeira requisição não dá erro: ela acorda o serviço, e isso leva de
    trinta segundos a mais de um minuto. Com o timeout normal de 15 s, essa
    requisição falharia e o usuário veria uma tela vazia sem explicação.

    Por isso a primeira chamada da sessão é feita aqui, contra a rota `/`
    (que não exige chave), com um tempo de espera bem maior. Roda uma única
    vez por sessão — as chamadas seguintes usam o timeout normal.
    """
    if st.session_state.get("_api_acordada"):
        return True
    try:
        requests.get(f"{API_URL}/", timeout=_TIMEOUT_ACORDAR)
        st.session_state["_api_acordada"] = True
        return True
    except requests.RequestException:
        return False


def ultimo_erro() -> str | None:
    """Devolve e limpa a última falha de rede, para a página exibir um aviso."""
    return st.session_state.pop("_ultimo_erro", None)


def limpar_cache() -> None:
    """
    Descarta todas as respostas memorizadas.

    Chamado depois de gravar um equipamento: sem isso a lista continuaria
    mostrando os dados anteriores até o cache expirar.
    """
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Equipamentos
# ---------------------------------------------------------------------------

@st.cache_data(ttl=120, show_spinner=False)
def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos", feature="equipamentos") or []


@st.cache_data(ttl=120, show_spinner=False)
def tags_disponiveis() -> list[str]:
    return _get("/v1/equipamentos/tags", feature="equipamentos") or []


@st.cache_data(ttl=60, show_spinner=False)
def buscar_por_tag(tag: str) -> dict | None:
    return _get(f"/v1/equipamentos/{tag}", feature="equipamentos")


def salvar(dados: dict) -> tuple[bool, str]:
    """Escrita — nunca memorizada."""
    return _post("/v1/equipamentos", dados)


# ---------------------------------------------------------------------------
# Plantas
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600, show_spinner=False)
def listar_plantas() -> list[str]:
    return _get("/v1/plantas", feature="plantas") or []


@st.cache_data(ttl=600, show_spinner=False)
def listar_areas(planta: str) -> list[str]:
    if not planta:
        return []
    return _get(f"/v1/plantas/{planta}/areas", feature="plantas") or []


@st.cache_data(ttl=600, show_spinner=False)
def listar_equipamentos(planta: str, area: str) -> list[str]:
    if not planta or not area:
        return []
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos", feature="plantas") or []


@st.cache_data(ttl=600, show_spinner=False)
def buscar_localizacao(tag: str) -> tuple[str, str]:
    loc = _get(f"/v1/plantas/localizacao/{tag}", feature="plantas")
    if not loc:
        return "", ""
    return loc["planta"], loc["area"]


# ---------------------------------------------------------------------------
# Sensores — TTL curto: telemetria envelhece rápido
# ---------------------------------------------------------------------------

@st.cache_data(ttl=20, show_spinner=False)
def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual", feature="sensores") or {
        "tag": tag, "timestamp": "", "tensao_v": 0, "corrente_a": 0,
        "temp_c": 0, "vibracao_mms": 0, "rotacao_rpm": 0, "falha": 0,
        "severidade_temp": "normal", "severidade_vibracao": "normal",
    }


@st.cache_data(ttl=20, show_spinner=False)
def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    return _get(f"/v1/sensores/{tag}/historico", feature="sensores", params={"n": n_pontos}) or []
