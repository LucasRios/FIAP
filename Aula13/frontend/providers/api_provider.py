# =============================================================================
# frontend/providers/api_provider.py — Aula 13: Consumindo a API no Front
#
# Responsabilidade: centralizar TODAS as chamadas HTTP para o back-end FastAPI
# (o main.py que construímos na Aula 12) num único lugar. É o mesmo papel que
# os providers/*.py tinham no Semestre 1 (Aula 06) — só que agora, em vez de
# chamar o modelo de IA diretamente, este provider faz uma requisição de rede.
#
# NOVO NESTA AULA: todo este arquivo. É a peça central da Aula 13.
#
# Como instalar:
#   pip install requests streamlit
# =============================================================================

import requests
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA API
# -----------------------------------------------------------------------------
# st.secrets lê valores do arquivo .streamlit/secrets.toml (que NUNCA deve ser
# commitado no Git). Usamos .get(...) com um valor padrão para que o código
# também funcione em desenvolvimento local, mesmo sem o arquivo de secrets.
API_URL = st.secrets.get("API_URL", "http://localhost:8000")
API_KEY = st.secrets.get("API_KEY", "")  # NOVO NESTA AULA: autenticação por API Key

# Cabeçalhos (headers) enviados em TODAS as chamadas.
# X-API-Key é o header que o back-end (Aula 12/13) espera para autenticar.
_HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL: analisar_sentimento
# -----------------------------------------------------------------------------
# Esta função substitui a chamada direta ao provider de IA que existia no
# Semestre 1. Agora, em vez de rodar o modelo aqui dentro do Streamlit, nós
# fazemos um requests.post para o servidor FastAPI e esperamos a resposta.
def analisar_sentimento(texto: str) -> dict | None:
    """
    Chama o endpoint /v1/analise/sentimento do back-end FastAPI.

    Args:
        texto: o texto que o usuário digitou na interface.

    Returns:
        Um dicionário com "sentimento" e "confianca" em caso de sucesso,
        ou None se qualquer coisa der errado (o motivo específico já foi
        exibido ao usuário via st.error/st.warning dentro desta função).
    """
    try:
        # timeout=10 evita que o app fique "travado" para sempre esperando
        # uma resposta que talvez nunca chegue (ex: servidor caiu).
        resposta = requests.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            headers=_HEADERS,
            timeout=10,
        )

        # -------------------------------------------------------------
        # TRATAMENTO DE ERROS — NOVO NESTA AULA
        # -------------------------------------------------------------
        # Um front-end de produção NUNCA mostra o erro técnico cru para
        # o usuário. Aqui traduzimos cada status_code numa mensagem clara.
        if resposta.status_code == 200:
            return resposta.json()

        elif resposta.status_code == 422:
            # 422 = os dados enviados não passaram na validação do Pydantic
            # (ver EntradaAnalise no backend/main.py da Aula 12)
            st.warning("Os dados enviados são inválidos. Verifique o texto e tente novamente.")

        elif resposta.status_code == 401:
            # 401 = a API Key enviada não confere com a esperada no servidor
            st.error("Sessão expirada ou chave inválida. Faça login novamente.")

        elif resposta.status_code == 500:
            st.error("Ocorreu um erro no servidor. Tente novamente em instantes.")

        else:
            st.error(f"Erro inesperado ({resposta.status_code}).")

    # requests.exceptions cobre problemas de REDE, não de validação de dados
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor. Verifique se o back-end está rodando.")

    except requests.exceptions.Timeout:
        st.error("A requisição demorou demais. O servidor pode estar sobrecarregado.")

    # Se chegou até aqui, algo falhou — retornamos None para o chamador saber
    # que não há resultado válido para exibir.
    return None
