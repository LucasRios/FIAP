# Aula 4 — Workshop: Refatorando o Sprint com FastAPI

## Objetivo

Transformar o projeto do Sprint — onde o provider acessa o modelo e os dados diretamente dentro do Streamlit/Gradio — em uma arquitetura separada, com FastAPI no back-end e o front apenas consumindo via HTTP. Aplicar segurança real com variáveis de ambiente e proteção de rotas.

---

# 1. O Ponto de Partida

No Sprint do semestre 1, a arquitetura era assim:

```
app.py (Streamlit)
  └─ features/news_analysis/page.py
       └─ pipelines/news_pipeline.py
            └─ providers/scraper_nlp_provider.py   ← acessa NLP direto
            └─ providers/dataset_estruturado.csv   ← lê arquivo local
```

O `scraper_nlp_provider.py` fazia duas coisas que pertencem ao back-end:
1. Buscava notícias de uma fonte externa
2. Rodava análise de NLP sobre elas

O Streamlit executava tudo isso dentro do seu próprio processo — o que significa que se dois usuários usassem o app ao mesmo tempo, dois processos de NLP rodariam em paralelo no mesmo servidor, competindo por memória e CPU.

---

# 2. O Que Vamos Mudar

```
# Antes — tudo junto
Streamlit → pipeline → provider (NLP direto)

# Depois — separado
Streamlit → api_provider → [HTTP] → FastAPI → pipeline → provider (NLP)
```

A regra que vai guiar a refatoração:

> **Se a lógica não é sobre exibir ou coletar dados do usuário, ela pertence ao back-end.**

Análise de NLP, chamada de modelo, leitura de banco de dados, scraping — tudo isso é back-end. O front-end deve apenas:
- Coletar entrada do usuário
- Exibir resultados
- Gerenciar estado da sessão

---

# 3. Criando o Back-end FastAPI

Vamos criar um servidor FastAPI que expõe as capacidades do Sprint como endpoints HTTP.

```
backend/
├── main.py
├── routers/
│   └── noticias.py
├── pipelines/
│   └── news_pipeline.py      ← copiado do Sprint
├── providers/
│   └── scraper_nlp_provider.py  ← copiado do Sprint
└── requirements.txt
```

```python
# backend/main.py
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from routers import noticias
import os

app = FastAPI(title="Sprint API", version="1.0.0")

# Segurança — API Key
api_key_header = APIKeyHeader(name="X-API-Key")
API_KEY = os.getenv("API_KEY", "chave-local-dev")

def verificar_chave(chave: str = Security(api_key_header)):
    if chave != API_KEY:
        raise HTTPException(status_code=401, detail="Chave inválida")
    return chave

# CORS para o Streamlit local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(noticias.router, prefix="/v1", tags=["Notícias"])
```

```python
# backend/routers/noticias.py
from fastapi import APIRouter, Security
from pydantic import BaseModel
from pipelines.news_pipeline import processar_noticia
from main import verificar_chave

router = APIRouter()

class EntradaNoticia(BaseModel):
    url: str | None = None
    texto: str | None = None

class ResultadoNoticia(BaseModel):
    resumo: str
    sentimento: str
    entidades: list[str]
    confianca: float

@router.post("/noticias/analisar", response_model=ResultadoNoticia)
def analisar_noticia(entrada: EntradaNoticia, _: str = Security(verificar_chave)):
    if not entrada.url and not entrada.texto:
        raise HTTPException(status_code=400, detail="Informe url ou texto.")

    resultado = processar_noticia(url=entrada.url, texto=entrada.texto)
    return resultado

@router.get("/noticias/historico")
def listar_historico(_: str = Security(verificar_chave)):
    # Retorna o histórico de análises da sessão
    return {"analises": []}
```

---

# 4. Adaptando o Front-end Streamlit

O front-end para de chamar o pipeline diretamente e passa a chamar o `api_provider`.

```python
# frontend/providers/api_provider.py
import requests
import streamlit as st

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
API_KEY = st.secrets.get("API_KEY", "chave-local-dev")

_HEADERS = {"X-API-Key": API_KEY}

def analisar_noticia(url: str = None, texto: str = None) -> dict | None:
    payload = {}
    if url:
        payload["url"] = url
    if texto:
        payload["texto"] = texto

    try:
        r = requests.post(
            f"{API_URL}/v1/noticias/analisar",
            json=payload,
            headers=_HEADERS,
            timeout=30   # NLP pode ser lento
        )
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            st.warning("Informe uma URL ou um texto para análise.")
        elif e.response.status_code == 401:
            st.error("Erro de autenticação com o servidor.")
        else:
            st.error(f"Erro do servidor: {e.response.status_code}")
    except requests.ConnectionError:
        st.error("Não foi possível conectar ao back-end. O servidor está rodando?")
    except requests.Timeout:
        st.error("A análise está demorando mais que o esperado. Tente novamente.")
    return None
```

```python
# frontend/features/news_analysis/page.py
import streamlit as st
from providers import api_provider

def render():
    st.subheader("Análise de Notícia")

    aba_url, aba_texto = st.tabs(["Analisar por URL", "Colar texto"])

    with aba_url:
        url = st.text_input("URL da notícia:")
        if st.button("Analisar URL") and url:
            with st.spinner("Analisando..."):
                resultado = api_provider.analisar_noticia(url=url)
            _exibir_resultado(resultado)

    with aba_texto:
        texto = st.text_area("Cole o texto da notícia:", height=200)
        if st.button("Analisar Texto") and texto:
            with st.spinner("Analisando..."):
                resultado = api_provider.analisar_noticia(texto=texto)
            _exibir_resultado(resultado)

def _exibir_resultado(resultado: dict | None):
    if not resultado:
        return

    col1, col2 = st.columns(2)
    col1.metric("Sentimento", resultado["sentimento"])
    col2.metric("Confiança", f"{resultado['confianca']:.0%}")

    st.markdown("### Resumo")
    st.write(resultado["resumo"])

    if resultado["entidades"]:
        st.markdown("### Entidades detectadas")
        st.write(", ".join(resultado["entidades"]))
```

---

# 5. Variáveis de Ambiente — Configuração sem Segredos no Código

Dois arquivos de configuração, um para cada lado:

```bash
# backend/.env  (nunca commitar)
API_KEY=chave-super-secreta-producao
DATABASE_URL=postgresql://usuario:senha@localhost/sprintdb
MODEL_NAME=claude-haiku-4-5-20251001
```

```toml
# frontend/.streamlit/secrets.toml  (nunca commitar)
API_URL = "http://localhost:8000"
API_KEY = "chave-super-secreta-producao"
```

```python
# backend/main.py — lendo as variáveis de ambiente
from dotenv import load_dotenv
import os

load_dotenv()  # carrega o .env automaticamente

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-haiku-4-5-20251001")

if not API_KEY:
    raise RuntimeError("API_KEY não configurada. Defina a variável de ambiente.")
```

```bash
pip install python-dotenv
```

O `.env` e `secrets.toml` devem estar no `.gitignore` — assim como fazíamos com `App.config` no ecossistema .NET.

---

# 6. Rodando a Arquitetura Completa

Com tudo separado, você precisa de dois terminais:

```bash
# Terminal 1 — back-end
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — front-end
cd frontend
streamlit run app.py
```

Verifique que tudo está funcionando:
1. Acesse `http://localhost:8000/docs` — veja os endpoints documentados
2. Teste um endpoint diretamente no Swagger
3. Acesse `http://localhost:8501` — use o Streamlit normalmente
4. Verifique no terminal do back-end que as requisições chegam

---

# 7. O Que Mudou e Por Que Vale a Pena

| Aspecto | Antes (monolito) | Depois (separado) |
|---------|------------------|-------------------|
| Escala | Front e back escalam juntos | Cada um escala de forma independente |
| Reutilização | Lógica presa ao Streamlit | Qualquer cliente pode usar a API |
| Testabilidade | Difícil testar o pipeline isolado | Pipeline testável via curl/Pytest |
| Deploy | Um processo só | Front e back fazem deploy separado |
| Segurança | Segredos misturados no app | Cada camada tem suas credenciais |

---

# Referências

- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [FastAPI — Security Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [12-Factor App — Config](https://12factor.net/config)
