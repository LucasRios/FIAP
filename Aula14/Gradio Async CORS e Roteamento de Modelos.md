# Aula 3 — Gradio, Async, CORS e Roteamento de Modelos

## Objetivo

Conectar o Gradio ao FastAPI, entender async/await no contexto de front-end de IA, resolver o problema de CORS que inevitavelmente aparece, e criar uma API com múltiplas rotas de modelos — incluindo versionamento e documentação como contrato entre times.

---

# 1. Gradio Consumindo FastAPI

Na aula anterior conectamos o Streamlit ao FastAPI com `requests` síncrono. O Gradio tem seu próprio modelo de eventos — cada função Python vinculada a um componente é disparada de forma independente. Isso cria uma oportunidade natural para chamadas HTTP assíncronas.

```python
import gradio as gr
import requests

API_URL = "http://localhost:8000"

def analisar_texto(texto: str) -> tuple[str, float]:
    """Função chamada pelo Gradio quando o usuário clica em Enviar."""
    resposta = requests.post(
        f"{API_URL}/v1/analise/sentimento",
        json={"texto": texto},
        headers={"X-API-Key": "minha-chave"},
        timeout=10
    )

    if resposta.status_code == 200:
        dados = resposta.json()
        return dados["sentimento"], dados["confianca"]
    else:
        return "erro", 0.0


with gr.Blocks(title="Análise de Sentimento") as demo:
    gr.Markdown("## Análise de Sentimento via FastAPI")

    with gr.Row():
        entrada = gr.Textbox(label="Texto", lines=4)

    with gr.Row():
        sentimento = gr.Textbox(label="Sentimento")
        confianca = gr.Number(label="Confiança")

    botao = gr.Button("Analisar")
    botao.click(
        fn=analisar_texto,
        inputs=[entrada],
        outputs=[sentimento, confianca]
    )

demo.launch()
```

---

# 2. Async/Await — Por que Importa para IA

Modelos de IA são lentos. Um modelo de linguagem pode levar 2, 5, até 10 segundos para responder. Se você usa funções síncronas (`requests.post`), o processo Python fica **bloqueado** esperando a resposta — não pode atender outra requisição, não pode atualizar a interface.

Funções assíncronas (`async def` + `await`) permitem que o processo faça outra coisa enquanto espera a resposta da rede.

```python
import gradio as gr
import httpx  # alternativa assíncrona ao requests

API_URL = "http://localhost:8000"
API_KEY = "minha-chave"

async def analisar_texto_async(texto: str) -> tuple[str, float]:
    """
    Versão assíncrona: não bloqueia o processo enquanto espera a API.
    httpx é o equivalente assíncrono do requests.
    """
    async with httpx.AsyncClient() as client:
        resposta = await client.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            headers={"X-API-Key": API_KEY},
            timeout=10.0
        )

    if resposta.status_code == 200:
        dados = resposta.json()
        return dados["sentimento"], dados["confianca"]

    return f"Erro {resposta.status_code}", 0.0


with gr.Blocks() as demo:
    entrada = gr.Textbox(label="Texto")
    sentimento = gr.Textbox(label="Sentimento")
    confianca = gr.Number(label="Confiança")

    gr.Button("Analisar").click(
        fn=analisar_texto_async,
        inputs=[entrada],
        outputs=[sentimento, confianca]
    )

demo.launch()
```

```bash
pip install httpx
```

| | `requests` (síncrono) | `httpx` (assíncrono) |
|---|---|---|
| Espera a resposta? | Sim, bloqueia | Não, libera o processo |
| Múltiplos usuários simultâneos | Um por vez | Muitos em paralelo |
| Streaming de tokens | Não nativo | Nativo com `async for` |
| Complexidade | Menor | Maior |

Para aulas e protótipos, `requests` é suficiente. Para produção com múltiplos usuários ou streaming, `httpx` é a escolha.

---

# 3. CORS — O Erro que Todo Mundo Encontra

CORS (Cross-Origin Resource Sharing) é uma política de segurança dos navegadores. Quando um front-end rodando em `http://localhost:8501` tenta chamar uma API em `http://localhost:8000`, o navegador verifica se o servidor permite essa origem.

Se não permitir, você vê este erro no console:

```
Access to fetch at 'http://localhost:8000/v1/analise/sentimento'
from origin 'http://localhost:8501' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present.
```

O Streamlit e o Gradio fazem chamadas HTTP pelo **servidor Python**, não pelo navegador — então CORS não afeta chamadas feitas com `requests` ou `httpx` no back-end do Streamlit/Gradio. Mas **quando você usar o Gradio Client** ou qualquer JavaScript rodando no browser chamando sua API diretamente, CORS vai aparecer.

A solução está no FastAPI:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Lista de origens permitidas
ORIGENS_PERMITIDAS = [
    "http://localhost:8501",   # Streamlit local
    "http://localhost:7860",   # Gradio local
    "https://meuapp.streamlit.app",  # Streamlit Cloud (produção)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Nunca use `allow_origins=["*"]` em produção.** Isso permite que qualquer site na internet chame sua API, abrindo brechas de segurança. Em desenvolvimento, é aceitável para agilizar testes.

---

# 4. Roteamento de Modelos

Aplicações de IA raramente têm um único modelo. Um produto real pode ter:
- Um modelo leve para análise rápida
- Um modelo pesado para análise aprofundada
- Um modelo de uma versão anterior (para comparação A/B)
- Modelos especializados por domínio (saúde, jurídico, financeiro)

O FastAPI facilita a organização dessas rotas:

```python
# routers/analise.py
from fastapi import APIRouter
from pydantic import BaseModel
from providers import modelo_leve, modelo_pesado

router = APIRouter()

class EntradaTexto(BaseModel):
    texto: str

# Rota v1 — modelo leve, rápido
@router.post("/v1/analise/sentimento")
def sentimento_v1(entrada: EntradaTexto):
    return modelo_leve.analisar(entrada.texto)

# Rota v1 — sumarização
@router.post("/v1/analise/resumo")
def resumo_v1(entrada: EntradaTexto):
    return modelo_leve.resumir(entrada.texto)

# Rota v1 — classificação de categoria
@router.post("/v1/analise/classificar")
def classificar_v1(entrada: EntradaTexto):
    return modelo_leve.classificar(entrada.texto)

# Rota v2 — modelo pesado, análise mais rica
@router.post("/v2/analise/sentimento")
def sentimento_v2(entrada: EntradaTexto):
    # v2 usa um modelo mais robusto e retorna mais detalhes
    return modelo_pesado.analisar_completo(entrada.texto)
```

O front-end pode escolher qual rota usar baseado no contexto:

```python
# providers/api_provider.py no Streamlit
def analisar_sentimento(texto: str, modo: str = "rapido") -> dict | None:
    rota = "/v1/analise/sentimento" if modo == "rapido" else "/v2/analise/sentimento"

    try:
        r = requests.post(f"{API_URL}{rota}", json={"texto": texto}, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
```

```python
# features/analise/page.py
modo = st.radio("Modo de análise:", ["rapido", "detalhado"])
resultado = api_provider.analisar_sentimento(texto, modo=modo)
```

---

# 5. Documentação como Contrato

O Swagger UI gerado automaticamente pelo FastAPI (`/docs`) não é só uma conveniência de desenvolvimento — ele é o **contrato entre o time de front-end e o time de back-end**.

Boas práticas para manter a documentação útil:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de IA — FIAP",
    description="API de processamento de texto com modelos de linguagem.",
    version="1.0.0",
)

class EntradaTexto(BaseModel):
    texto: str = Field(
        ...,
        description="Texto a ser analisado",
        example="O produto chegou com defeito e a entrega atrasou."
    )
    idioma: str = Field(
        default="pt",
        description="Código do idioma (ISO 639-1)",
        example="pt"
    )

class ResultadoSentimento(BaseModel):
    sentimento: str = Field(..., description="'positivo', 'negativo' ou 'neutro'")
    confianca: float = Field(..., description="Score de 0.0 a 1.0", ge=0.0, le=1.0)
    tokens_usados: int = Field(..., description="Tokens consumidos na inferência")

@app.post(
    "/v1/analise/sentimento",
    response_model=ResultadoSentimento,
    summary="Análise de sentimento",
    description="Classifica o texto como positivo, negativo ou neutro e retorna o score de confiança.",
    tags=["Análise"]
)
def analisar_sentimento(entrada: EntradaTexto):
    ...
```

Com isso, `/docs` mostra exemplos reais, descrições dos campos e permite testar direto no browser — sem precisar do front-end pronto.

---

# 6. Estratégias de Fallback

Modelos falham. A API pode estar sobrecarregada ou o modelo pode retornar um resultado inválido. O front-end precisa ter uma estratégia de fallback clara.

```python
# providers/api_provider.py
def analisar_sentimento(texto: str) -> dict:
    """
    Tenta v2 primeiro (mais preciso). Se falhar, tenta v1.
    Se ambos falharem, retorna um resultado padrão seguro.
    """
    for versao in ["/v2/analise/sentimento", "/v1/analise/sentimento"]:
        try:
            r = requests.post(f"{API_URL}{versao}", json={"texto": texto},
                              headers=_HEADERS, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue

    # Fallback seguro — nunca retorna None para o front
    return {"sentimento": "indefinido", "confianca": 0.0, "tokens_usados": 0}
```

O fallback seguro garante que o front-end sempre recebe um dicionário com a estrutura esperada, mesmo em caso de falha total — evitando erros de `KeyError` na interface.

---

# Referências

- [HTTPX — Async HTTP Client](https://www.python-httpx.org)
- [FastAPI — CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI — Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [MDN — CORS](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/CORS)
- [REST API Versioning](https://restfulapi.net/versioning/)
