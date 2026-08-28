# Aula 13 — Consumindo a API no Front com Streamlit

## Objetivo

Conectar o Streamlit ao FastAPI usando a biblioteca `requests`, desta vez construindo um **chatbot** que conversa com o Gemini através do back-end da Aula 1. Tratar erros de forma que o usuário entenda o que aconteceu. Introduzir autenticação — via header customizado (API Key) e via **Bearer Token** — a primeira camada de segurança que todo front-end de IA precisa implementar.

---

# 1. O Papel do Front-end como Cliente HTTP

Na Aula 0 vimos que o front-end é o cliente da API. Agora vamos implementar isso. O Streamlit vai parar de chamar o Gemini diretamente e vai passar a fazer requisições HTTP para o FastAPI que construímos na Aula 1.

```
# Antes
Streamlit → google-genai → modelo

# Depois
Streamlit (chat) → requests.post(...) → FastAPI → google-genai → modelo
```

A mudança parece simples, mas ela habilita:
- Qualquer outro front-end (Gradio, mobile, outro time) pode consumir o mesmo back
- O modelo pode ser atualizado sem tocar no front
- O back-end pode escalar independentemente
- O back-end pode manter o histórico da conversa em memória de forma centralizada

---

# 2. A Biblioteca requests

`requests` é a biblioteca HTTP padrão de Python. Se você instalou dependências no semestre 1 para conectar APIs externas (Aula 05), você já a usou. Agora vamos usá-la para chamar nossa própria API.

```bash
pip install requests
```

```python
import requests

resposta = requests.post(
    "http://localhost:8000/v1/chat",
    json={"mensagem": "Oi, tudo bem?"}
)

resposta.status_code   # 200, 422, 500...
resposta.json()        # o corpo em dicionário Python
resposta.text          # o corpo como string bruta
resposta.headers       # os headers da resposta
```

---

# 3. O Backend: Endpoint de Chat com Gemini

Na Aula 1 construímos `/v1/classificar`. Agora vamos construir `/v1/chat`, seguindo a mesma arquitetura em camadas (rota → provider → modelo), mas com duas diferenças importantes: o endpoint mantém **histórico de conversa** e fica protegido por **autenticação**.

## 3.1 Estrutura de projeto

```
meu_projeto_backend/
├── main.py                  ← cria o app, inclui os routers
├── routers/
│   └── chat.py               ← endpoint /v1/chat
├── models/
│   ├── entrada.py            ← Pydantic de request
│   └── saida.py              ← Pydantic de response
├── providers/
│   └── gemini_provider.py    ← toda a lógica de chamada ao Gemini
├── auth/
│   └── seguranca.py          ← validação de API Key / Bearer Token
├── .env
└── requirements.txt
```

Essa separação é a mesma proposta na Aula 1: o `provider` não sabe que existe um FastAPI, e o `router` não sabe como o Gemini funciona por dentro. Trocar de modelo, ou até de fornecedor de IA, significa mexer só no `provider`.

## 3.2 O provider — `providers/gemini_provider.py`

```python
"""
Provider responsável por toda a comunicação com o Gemini.
Isolado do FastAPI: pode ser testado ou reaproveitado sem nenhum router.
"""

import os
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv() 

MODELO = "gemini-3.5-flash"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

CONFIG = types.GenerateContentConfig(
    system_instruction=(
        "Você é um assistente de chat útil e direto. "
        "Responda de forma clara e objetiva."
    ),
    max_output_tokens=800,
    temperature=0.7,  # chat se beneficia de alguma variação, diferente da classificação
    thinking_config=types.ThinkingConfig(thinking_budget=0),
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


async def enviar_mensagem(historico: list[dict], mensagem: str) -> str:
    """
    Envia o histórico da conversa + a nova mensagem ao Gemini.
    `historico` é uma lista de dicts no formato {"role": "user"|"model", "text": "..."}.
    """
    # Monta os `contents` no formato que a API do Gemini espera:
    # uma lista alternando turnos de usuário e do modelo.
    contents = [
        types.Content(role=turno["role"], parts=[types.Part(text=turno["text"])])
        for turno in historico
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=mensagem)]))

    resposta = await client.aio.models.generate_content(
        model=MODELO,
        contents=contents,
        config=CONFIG,
    )

    if not resposta.text:
        raise ValueError("Resposta vazia ou bloqueada pelo modelo")

    return resposta.text.strip()
```

## 3.3 Os contratos — `models/entrada.py` e `models/saida.py`

```python
# models/entrada.py
from pydantic import BaseModel, Field


class Turno(BaseModel):
    """Um turno já ocorrido na conversa, enviado pelo front a cada requisição."""
    role: str = Field(pattern="^(user|model)$")
    text: str


class EntradaChat(BaseModel):
    mensagem: str = Field(min_length=1, max_length=4000)
    historico: list[Turno] = Field(default_factory=list)
```

```python
# models/saida.py
from pydantic import BaseModel


class SaidaChat(BaseModel):
    resposta: str
```

O front-end é responsável por guardar e reenviar o histórico a cada chamada — o back-end aqui é **stateless**: não guarda sessão de ninguém. É a forma mais simples de escalar (qualquer instância do FastAPI pode atender qualquer requisição, já que nada fica em memória local do servidor).

## 3.4 O router — `routers/chat.py`

```python
from fastapi import APIRouter, HTTPException, Depends

from models.entrada import EntradaChat
from models.saida import SaidaChat
from providers import gemini_provider
from auth.seguranca import validar_credenciais

router = APIRouter()

#router = APIRouter(dependencies=[Depends(validar_credenciais)])

#@router.post("/", response_model=SaidaChat)
#async def conversar(entrada: EntradaChat):
#    ...


@router.post("/", response_model=SaidaChat)
async def conversar(entrada: EntradaChat, _=Depends(validar_credenciais)):
    """Recebe mensagem + histórico e devolve a resposta do Gemini."""
    historico = [{"role": t.role, "text": t.text} for t in entrada.historico]

    try:
        texto_resposta = await gemini_provider.enviar_mensagem(historico, entrada.mensagem)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Falha ao consultar o modelo") from exc

    return SaidaChat(resposta=texto_resposta)
```

## 3.5 O `main.py`

```python
from fastapi import FastAPI
from routers import chat

#app = FastAPI(
#    title="API de Chat com IA",
#    version="1.0.0",
#    dependencies=[Depends(validar_credenciais)]
#)


app = FastAPI(title="API de Chat com IA", version="1.0.0")

#app.include_router(
#    chat.router,
#    prefix="/v1/chat",
#    tags=["Chat"],
#    dependencies=[Depends(validar_credenciais)])


app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
```

```bash
uvicorn main:app --reload --port 8000
```

---

# 4. Autenticação — Duas Formas de Proteger a API

Toda API exposta na internet precisa de autenticação. Vamos implementar as duas formas mais comuns, no mesmo módulo, para comparar.

## 4.1 API Key em header customizado

O padrão que já vimos: uma string secreta enviada em um header próprio (`X-API-Key`). Simples, direto, muito usado entre serviços internos.

## 4.2 Bearer Token

Padrão do cabeçalho HTTP `Authorization`, usado pela maioria das APIs públicas (inclusive a própria OpenAI e Anthropic). O cliente envia:

```
Authorization: Bearer <token>
```

É o mesmo mecanismo por trás de JWT e OAuth2 — aqui usamos a versão mais simples, um token fixo, mas a forma de transporte é a mesma que você vai encontrar em produção.

## 4.3 Implementando os dois — `auth/seguranca.py`

```python
"""
Duas estratégias de autenticação para o mesmo endpoint:
- X-API-Key (header customizado)
- Authorization: Bearer <token>

Qualquer uma das duas, se válida, libera o acesso.
Isso é só para fins didáticos de comparação; em produção normalmente
se escolhe UMA estratégia e se mantém consistente em toda a API.
"""

import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

API_KEY_VALIDA = os.getenv("API_KEY")
BEARER_TOKEN_VALIDO = os.getenv("BEARER_TOKEN")

# Declaram QUAL header o Swagger deve pedir e documentar automaticamente.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def validar_credenciais(
    api_key: str = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    """
    Aceita autenticação por X-API-Key OU por Bearer Token.
    auto_error=False em ambos os schemes evita que o FastAPI dispare
    erro antes de checarmos as duas alternativas manualmente.
    """
    if api_key and api_key == API_KEY_VALIDA:
        return "api_key"

    if bearer and bearer.credentials == BEARER_TOKEN_VALIDO:
        return "bearer_token"

    raise HTTPException(status_code=401, detail="Credenciais inválidas ou ausentes")
```

```python
# .env do backend
GEMINI_API_KEY=chave_real_do_ai_studio
API_KEY=minha-chave-secreta-aqui
BEARER_TOKEN=um-token-fixo-para-fins-didaticos
```
```python
"""
Gera uma chave/token seguro para usar como API_KEY ou BEARER_TOKEN no .env.
Execução: python gerar_chave.py
"""
 
import secrets
 
 
def gerar_urlsafe(tamanho_bytes: int = 32) -> str:
    """Formato compacto, seguro para header HTTP. Recomendado."""
    return secrets.token_urlsafe(tamanho_bytes)
 
 
def gerar_hex(tamanho_bytes: int = 32) -> str:
    """Formato hexadecimal, mais longo, só caracteres 0-9a-f."""
    return secrets.token_hex(tamanho_bytes)
 
 
if __name__ == "__main__":
    print("token_urlsafe:", gerar_urlsafe())
    print("token_hex:    ", gerar_hex())
```
## 4.4 O que NÃO fazer

```python
# NUNCA faça isso — a key/token fica exposta no código
API_KEY = "abc123secreto"

# NUNCA faça isso — vaza no histórico do git
requests.post(url, headers={"X-API-Key": "abc123secreto"})
```

---

# 5. Tratamento de Erros no Front — Protótipo vs. Produto

Um front-end de produção nunca expõe erros técnicos diretamente para o usuário.

| Situação | Status Code | O que o usuário deve ver |
|----------|-------------|--------------------------|
| Back-end fora do ar | Exceção de conexão | "Serviço temporariamente indisponível" |
| Dados inválidos enviados | 422 | "Verifique a mensagem e tente novamente" |
| Não autorizado | 401 | "Sessão expirada, faça login novamente" |
| Erro ao consultar o modelo | 502 | "Não foi possível gerar a resposta agora" |
| Erro interno do servidor | 500 | "Ocorreu um erro. Tente novamente em instantes" |

---

# 6. Evoluindo a Autenticação para Bearer Token

Até aqui o `BEARER_TOKEN` era só uma string fixa no `.env`, comparada com `==`. Funciona, mas não é um JWT de verdade — é uma API Key disfarçada de Bearer Token, sem nenhuma das vantagens reais do padrão: expiração automática, claims (identidade de quem fez login) e validação sem depender de um valor fixo compartilhado.

Vamos evoluir para um **JWT (JSON Web Token)** de verdade:

```
header.payload.signature
```

- **header**: algoritmo usado (`HS256`)
- **payload**: claims — `sub` (usuário), `iat` (quando foi emitido), `exp` (quando expira)
- **signature**: `HMACSHA256(header + "." + payload, JWT_SECRET)` — garante que ninguém alterou o conteúdo sem saber o segredo

A diferença prática: em vez de todo cliente carregar o mesmo token fixo para sempre, o back-end passa a ter um **endpoint de login** que gera um token novo, assinado, com prazo de validade. O front chama esse endpoint uma vez, guarda o token, e reenvia em cada requisição até ele expirar.

## 6.1 O que muda na estrutura de projeto

```
meu_projeto_backend/
├── main.py
├── routers/
│   ├── chat.py
│   └── login.py               ← NOVO — endpoint /v1/login
├── models/
│   ├── entrada.py
│   ├── saida.py
│   └── login.py                ← NOVO — Pydantic do login
├── providers/
│   └── gemini_provider.py
├── auth/
│   └── seguranca.py            ← ALTERADO — agora gera e valida JWT
├── .env                         ← ALTERADO
└── requirements.txt              ← ALTERADO — adiciona pyjwt
```

## 6.2 Dependência nova

```bash
pip install pyjwt
```

```
# requirements.txt
fastapi
uvicorn
google-genai
python-dotenv
pyjwt
```

## 6.3 `.env` — trocando `BEARER_TOKEN` fixo por `JWT_SECRET`

```python
# .env do backend
GEMINI_API_KEY=chave_real_do_ai_studio
API_KEY=minha-chave-secreta-aqui

# antes: BEARER_TOKEN=um-token-fixo-para-fins-didaticos
# agora: um segredo usado para ASSINAR os tokens, não um token em si
JWT_SECRET=troque-por-uma-string-longa-e-aleatoria

# usuário fixo só para fins didáticos — em produção viria de um banco com senha com hash (bcrypt/argon2)
APP_USER=aluno
APP_PASSWORD=1234
```

O `gerar_chave.py` da seção anterior continua útil — use `token_urlsafe(32)` para gerar o `JWT_SECRET`.

## 6.4 `models/login.py` — contrato do login

```python
"""Pydantic do endpoint de login."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

## 6.5 `auth/seguranca.py` — de token fixo para JWT real

```python
"""
Duas estratégias de autenticação para o mesmo endpoint:
- X-API-Key (header customizado, string fixa — inalterado)
- Authorization: Bearer <token> (agora um JWT gerado no login, não mais fixo)

Qualquer uma das duas, se válida, libera o acesso.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

API_KEY_VALIDA = os.getenv("API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
EXPIRA_MINUTOS = 60

USUARIO_VALIDO = os.getenv("APP_USER")
SENHA_VALIDA = os.getenv("APP_PASSWORD")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def gerar_token(usuario: str) -> str:
    """
    NOVO. Cria o JWT assinado com HS256, usado pelo endpoint de login.
    exp faz o token expirar sozinho — sem precisar de blacklist manual.
    """
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario,
        "iat": agora,
        "exp": agora + timedelta(minutes=EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def autenticar_usuario(usuario: str, senha: str) -> bool:
    """NOVO. Checagem simples de credenciais — usada só pelo /v1/login."""
    return usuario == USUARIO_VALIDO and senha == SENHA_VALIDA


def validar_credenciais(
    api_key: str = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    """
    ALTERADO: a checagem do Bearer não é mais `bearer.credentials == BEARER_TOKEN_VALIDO`.
    Agora decodifica o JWT e valida assinatura + expiração via jwt.decode.
    """
    if api_key and api_key == API_KEY_VALIDA:
        return "api_key"

    if bearer:
        try:
            payload = jwt.decode(bearer.credentials, JWT_SECRET, algorithms=[ALGORITHM])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

    raise HTTPException(status_code=401, detail="Credenciais inválidas ou ausentes")
```

## 6.6 `routers/login.py` — NOVO endpoint

```python
from fastapi import APIRouter, HTTPException

from models.login import LoginRequest, LoginResponse
from auth.seguranca import autenticar_usuario, gerar_token

router = APIRouter()


@router.post("/", response_model=LoginResponse)
def login(dados: LoginRequest):
    """Valida usuário/senha e devolve um JWT novo, válido por EXPIRA_MINUTOS."""
    if not autenticar_usuario(dados.usuario, dados.senha):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    return LoginResponse(access_token=gerar_token(dados.usuario))
```

## 6.7 `main.py` — registrando o novo router

```python
from fastapi import FastAPI
from routers import chat, login   # login adicionado

app = FastAPI(title="API de Chat com IA", version="1.0.0")

app.include_router(login.router, prefix="/v1/login", tags=["Login"])   # NOVO
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
```

`routers/chat.py` **não muda** — `validar_credenciais` continua sendo a mesma dependency injetada, só o que acontece dentro dela mudou.

---

# 7. O Front-end: Chatbot com Login e Bearer Token (JWT)

Antes o front só carregava um `BEARER_TOKEN` fixo do `secrets.toml`. Agora ele precisa **fazer login primeiro**, guardar o token retornado em `st.session_state`, e reenviá-lo em cada chamada — tratando também o caso de token expirado.

## 7.1 `.streamlit/secrets.toml` do front

```toml
API_URL = "http://localhost:8000"

# credenciais de login, não mais um token fixo
APP_USER = "aluno"
APP_PASSWORD = "1234"
```

## 7.2 `providers/api_provider.py` — com login e token dinâmico

```python
"""
Todas as chamadas HTTP do front para o back ficam centralizadas aqui.
Agora inclui a função de login, que obtém o JWT usado nas chamadas seguintes.
"""

import requests
import streamlit as st

API_URL = st.secrets.get("API_URL", "http://localhost:8000")


def login(usuario: str, senha: str) -> bool:
    """
    NOVO. Autentica no back-end e guarda o JWT em st.session_state.
    Retorna True se o login deu certo.
    """
    try:
        r = requests.post(
            f"{API_URL}/v1/login/",
            json={"usuario": usuario, "senha": senha},
            timeout=10,
        )
        r.raise_for_status()
        st.session_state.access_token = r.json()["access_token"]
        return True
    except requests.HTTPError:
        st.error("Usuário ou senha inválidos.")
    except requests.ConnectionError:
        st.error("Não foi possível conectar ao servidor.")
    return False


def enviar_mensagem(mensagem: str, historico: list[dict]) -> str | None:
    """
    ALTERADO: o header Authorization agora usa o token guardado na sessão
    (obtido no login), não mais um valor fixo do secrets.toml.
    """
    token = st.session_state.get("access_token")
    if not token:
        st.error("Faça login antes de enviar mensagens.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            f"{API_URL}/v1/chat/",
            json={"mensagem": mensagem, "historico": historico},
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["resposta"]

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            # ALTERADO: token expirado — limpa a sessão e força novo login
            st.session_state.access_token = None
            st.error("Sessão expirada. Faça login novamente.")
        elif e.response.status_code == 422:
            st.warning("Mensagem inválida. Tente novamente.")
        elif e.response.status_code == 502:
            st.error("Não foi possível gerar a resposta agora.")
        else:
            st.error(f"Erro {e.response.status_code}.")
    except requests.ConnectionError:
        st.error("Não foi possível conectar ao servidor. Verifique se o back-end está rodando.")
    except requests.Timeout:
        st.error("A requisição demorou demais. Tente novamente.")

    return None
```

## 7.3 `app.py` — tela de login antes do chat

```python
# app.py
import streamlit as st
from providers import api_provider

st.set_page_config(page_title="Chat com IA", layout="centered")
st.title("Chat com IA")

if "historico" not in st.session_state:
    st.session_state.historico = []  # [{"role": "user"|"model", "text": "..."}]

if "access_token" not in st.session_state:
    st.session_state.access_token = None

# NOVO: sem token, mostra formulário de login e para por aqui
if not st.session_state.access_token:
    st.subheader("Login")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar and api_provider.login(usuario, senha):
        st.rerun()

    st.stop()  # impede o restante da página de renderizar sem estar logado

# a partir daqui, o resto do chat é idêntico ao da seção 7 original
for turno in st.session_state.historico:
    papel_exibicao = "user" if turno["role"] == "user" else "assistant"
    with st.chat_message(papel_exibicao):
        st.markdown(turno["text"])

mensagem = st.chat_input("Digite sua mensagem...")

if mensagem:
    with st.chat_message("user"):
        st.markdown(mensagem)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta = api_provider.enviar_mensagem(mensagem, st.session_state.historico)

        if resposta:
            st.markdown(resposta)

    if resposta:
        st.session_state.historico.append({"role": "user", "text": mensagem})
        st.session_state.historico.append({"role": "model", "text": resposta})
```

## 7.4 Testando

```bash
# Terminal 1 — back-end
uvicorn main:app --reload --port 8000

# Terminal 2 — front-end
streamlit run app.py
```

No Swagger (`http://localhost:8000/docs`), chame `POST /v1/login/` primeiro para obter o token, clique em **Authorize** e cole `Bearer <token>` para testar `/v1/chat/` isoladamente — só então vale testar pelo Streamlit.


---

# Referências

- [Requests — Documentação](https://requests.readthedocs.io)
- [FastAPI — Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI — HTTPBearer](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer)
- [Streamlit — Chat elements (`st.chat_message`, `st.chat_input`)](https://docs.streamlit.io/develop/api-reference/chat)
- [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
