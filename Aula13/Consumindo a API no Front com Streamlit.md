# Aula 2 — Consumindo a API no Front com Streamlit

## Objetivo

Conectar o Streamlit ao FastAPI criado na aula anterior usando a biblioteca `requests`. Tratar erros de forma que o usuário entenda o que aconteceu. Introduzir autenticação via API Key — a primeira camada de segurança que todo front-end de IA precisa implementar.

---

# 1. O Papel do Front-end como Cliente HTTP

Na Aula 0 vimos que o front-end é o cliente da API. Agora vamos implementar isso. O Streamlit vai parar de chamar o provider diretamente e vai passar a fazer requisições HTTP para o FastAPI.

```
# Antes
Streamlit → provider.py → modelo

# Depois
Streamlit → requests.post(...) → FastAPI → provider.py → modelo
```

A mudança parece simples, mas ela habilita:
- Qualquer outro front-end (Gradio, mobile, outro time) pode consumir o mesmo back
- O modelo pode ser atualizado sem tocar no front
- O back-end pode escalar independentemente

---

# 2. A Biblioteca requests

`requests` é a biblioteca HTTP padrão de Python. Se você instalou dependências no semestre 1 para conectar APIs externas (Aula 05), você já a usou. Agora vamos usá-la para chamar nossa própria API.

```bash
pip install requests
```

```python
import requests

# GET — buscar dados
resposta = requests.get("http://localhost:8000/v1/historico")

# POST — enviar dados para processamento
resposta = requests.post(
    "http://localhost:8000/v1/analise/sentimento",
    json={"texto": "O produto chegou com defeito."}
)

# A resposta sempre tem:
resposta.status_code   # 200, 422, 500...
resposta.json()        # o corpo em dicionário Python
resposta.text          # o corpo como string bruta
resposta.headers       # os headers da resposta
```

---

# 3. Integração Básica com Streamlit

O padrão mais simples: o usuário digita algo, clica em um botão, o Streamlit chama a API, e o resultado aparece na tela.

```python
import streamlit as st
import requests

st.set_page_config(page_title="Análise de Sentimento", layout="wide")
st.title("Análise de Sentimento")

API_URL = "http://localhost:8000"

texto = st.text_area("Digite o texto para análise:")
botao = st.button("Analisar")

if botao and texto:
    resposta = requests.post(
        f"{API_URL}/v1/analise/sentimento",
        json={"texto": texto}
    )
    resultado = resposta.json()
    st.write(f"Sentimento: {resultado['sentimento']}")
    st.write(f"Confiança: {resultado['confianca']:.0%}")
```

Isso funciona, mas tem um problema grave: **não trata erros**. Se a API estiver fora do ar, o Streamlit vai mostrar um erro Python feio para o usuário. Vamos corrigir isso.

---

# 4. Tratamento de Erros — A Diferença entre Protótipo e Produto

Um front-end de produção nunca expõe erros técnicos diretamente para o usuário. Erros de API podem acontecer por vários motivos:

| Situação | Status Code | O que o usuário deve ver |
|----------|-------------|--------------------------|
| Back-end fora do ar | Exceção de conexão | "Serviço temporariamente indisponível" |
| Dados inválidos enviados | 422 | "Verifique os dados e tente novamente" |
| Não autorizado | 401 | "Sessão expirada, faça login novamente" |
| Recurso não encontrado | 404 | "Análise não encontrada" |
| Erro interno do servidor | 500 | "Ocorreu um erro. Tente novamente em instantes" |

```python
import streamlit as st
import requests
from requests.exceptions import ConnectionError, Timeout

API_URL = "http://localhost:8000"

def chamar_api_sentimento(texto: str) -> dict | None:
    """
    Chama o endpoint de sentimento e trata todos os erros possíveis.
    Retorna o dicionário de resultado ou None em caso de falha.
    """
    try:
        resposta = requests.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            timeout=10  # não espera indefinidamente
        )

        if resposta.status_code == 200:
            return resposta.json()

        elif resposta.status_code == 422:
            st.warning("Os dados enviados são inválidos. Verifique o texto e tente novamente.")

        elif resposta.status_code == 401:
            st.error("Sessão expirada. Faça login novamente.")

        elif resposta.status_code == 500:
            st.error("Ocorreu um erro no servidor. Tente novamente em instantes.")

        else:
            st.error(f"Erro inesperado ({resposta.status_code}).")

    except ConnectionError:
        st.error("Não foi possível conectar ao servidor. Verifique se o back-end está rodando.")

    except Timeout:
        st.error("A requisição demorou demais. O servidor pode estar sobrecarregado.")

    return None


# Interface
st.title("Análise de Sentimento")
texto = st.text_area("Digite o texto:")

if st.button("Analisar") and texto:
    with st.spinner("Analisando..."):
        resultado = chamar_api_sentimento(texto)

    if resultado:
        col1, col2 = st.columns(2)
        col1.metric("Sentimento", resultado["sentimento"])
        col2.metric("Confiança", f"{resultado['confianca']:.0%}")
```

O `st.spinner` é um detalhe importante de UX: indica ao usuário que algo está acontecendo enquanto aguarda a resposta da API. Revise a Aula 02 do semestre 1 para relembrar os pilares de UX para IA — esta é a **Gestão de Expectativa e Incerteza** aplicada ao consumo de API.

---

# 5. Autenticação — API Key

Qualquer API exposta na internet precisa de autenticação. O padrão mais simples é a **API Key**: uma string secreta que o cliente envia no header de cada requisição. O servidor verifica se a key é válida antes de processar.

## No FastAPI (back-end)

```python
# main.py
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
import os

app = FastAPI()

# O header que o cliente deve enviar
api_key_header = APIKeyHeader(name="X-API-Key")

# A key válida vem de uma variável de ambiente — nunca hardcode
API_KEY_VALIDA = os.getenv("API_KEY")

def verificar_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY_VALIDA:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return api_key

@app.post("/v1/analise/sentimento")
def analisar(entrada: EntradaAnalise, api_key: str = Security(verificar_api_key)):
    # Se chegou aqui, a key foi validada
    return modelo_provider.classificar(entrada.texto)
```

## No Streamlit (front-end)

A API Key não pode estar no código — ela precisa vir de uma variável de ambiente ou de `st.secrets`.

```python
# .streamlit/secrets.toml  (nunca commitar esse arquivo)
API_KEY = "minha-chave-secreta-aqui"
API_URL = "http://localhost:8000"
```

```python
# app.py
import streamlit as st
import requests

# st.secrets lê o arquivo .streamlit/secrets.toml
API_KEY = st.secrets["API_KEY"]
API_URL = st.secrets["API_URL"]

def chamar_api_sentimento(texto: str) -> dict | None:
    try:
        resposta = requests.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            headers={"X-API-Key": API_KEY},  # a key vai no header
            timeout=10
        )
        if resposta.status_code == 200:
            return resposta.json()
        elif resposta.status_code == 401:
            st.error("Erro de autenticação com o servidor.")
        else:
            st.error(f"Erro {resposta.status_code}.")
    except Exception as e:
        st.error("Não foi possível conectar ao servidor.")
    return None
```

## O que NÃO fazer

```python
# NUNCA faça isso — a key fica exposta no código
API_KEY = "abc123secreto"

# NUNCA faça isso — vaza no histórico do git
requests.post(url, headers={"X-API-Key": "abc123secreto"})
```

---

# 6. Centralizando as Chamadas de API

Em projetos maiores, é boa prática centralizar todas as chamadas de API em um módulo separado — exatamente como fazíamos com os providers no semestre 1.

```
features/
  analise/
    page.py          ← interface Streamlit
    pipeline.py      ← orquestra a lógica
providers/
  api_provider.py    ← todas as chamadas HTTP ficam aqui
```

```python
# providers/api_provider.py
import requests
import streamlit as st

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
API_KEY = st.secrets.get("API_KEY", "")

# Cabeçalhos padrão enviados em todas as requisições
_HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def analisar_sentimento(texto: str) -> dict | None:
    try:
        r = requests.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            headers=_HEADERS,
            timeout=10
        )
        r.raise_for_status()  # lança exceção para qualquer 4xx ou 5xx
        return r.json()
    except requests.HTTPError as e:
        st.error(f"Erro da API: {e.response.status_code}")
    except requests.ConnectionError:
        st.error("Servidor indisponível.")
    except requests.Timeout:
        st.error("Tempo limite excedido.")
    return None

def listar_historico(pagina: int = 1) -> list | None:
    try:
        r = requests.get(
            f"{API_URL}/v1/historico",
            params={"pagina": pagina},
            headers=_HEADERS,
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        st.error("Não foi possível carregar o histórico.")
    return None
```

```python
# features/analise/page.py
import streamlit as st
from providers import api_provider

def render():
    st.subheader("Análise de Texto")
    texto = st.text_area("Texto:")

    if st.button("Analisar") and texto:
        with st.spinner("Processando..."):
            resultado = api_provider.analisar_sentimento(texto)

        if resultado:
            st.metric("Sentimento", resultado["sentimento"])
            st.metric("Confiança", f"{resultado['confianca']:.0%}")
```

Esse padrão é direto: se você precisar trocar a URL da API, mudar o header de autenticação ou adicionar retry logic, você muda em um único lugar — o `api_provider.py`.

---

# Referências

- [Requests — Documentação](https://requests.readthedocs.io)
- [FastAPI — Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
