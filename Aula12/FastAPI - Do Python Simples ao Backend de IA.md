# Aula 1 — FastAPI: Do Python Simples ao Backend de IA

## Objetivo

Entender por que um script Python puro não escala como produto, criar os primeiros endpoints com FastAPI e conectar esse novo conhecimento com a arquitetura modular que construímos na Aula 06 do semestre anterior.

---

# 1. O Problema do Script Isolado

No semestre anterior construímos aplicações onde o Streamlit ou o Gradio acessavam o modelo e o banco de dados diretamente — tudo no mesmo processo Python.

```
# Como estava no semestre 1
┌──────────────────────────────────────┐
│  app.py (Streamlit)                  │
│    └─ pipeline.py                    │
│         └─ provider.py  ←── modelo  │
│         └─ provider.py  ←── banco   │
└──────────────────────────────────────┘
```

Isso funcionou para protótipos. Mas imagine o seguinte cenário real:

**Problema 1 — Dois times, dois front-ends:**
O time A quer um dashboard Streamlit para analistas. O time B quer um app mobile. Se a lógica de IA está acoplada ao Streamlit, o time B precisa reescrever tudo.

**Problema 2 — Escala independente:**
O modelo de IA é pesado e precisa de GPU. A interface é leve e precisa de resposta rápida. Se os dois estão no mesmo processo, você escala tudo junto — caro e ineficiente.

**Problema 3 — Streamlit chamando Streamlit não é uma API:**
Se você criar um segundo app Streamlit para expor dados ao primeiro, você não tem controle sobre o contrato, versionamento, autenticação ou formato de resposta. Você tem dois scripts conversando de forma frágil.

A solução é separar as responsabilidades:

```
# Como vai ficar no semestre 2
┌──────────────────┐       ┌──────────────────────┐
│  Streamlit /     │──────▶│  FastAPI              │
│  Gradio (front)  │  HTTP │  └─ pipeline.py       │
└──────────────────┘       │       └─ provider.py  │
                           └──────────────────────┘
```

---

# 2. Por que FastAPI e não Flask ou Django

Três frameworks dominam APIs em Python. A escolha importa:

| Aspecto | Flask | Django | FastAPI |
|---------|-------|--------|---------|
| Curva de aprendizado | Baixa | Alta | Baixa |
| Validação de dados | Manual | Manual (Forms) | Automática (Pydantic) |
| Documentação automática | Não | Não | Sim (Swagger + ReDoc) |
| Performance | Média | Média | Alta (async nativo) |
| Tipagem | Opcional | Opcional | Central |
| Adoção em IA/ML | Moderada | Baixa | **Dominante** |

O FastAPI foi construído para o mundo moderno de APIs: validação automática via type hints, documentação gerada do código, async de primeira classe. Para aplicações de IA, onde os payloads precisam ser validados e a documentação precisa ser compartilhada entre times, ele é a escolha mais produtiva.

---

# 3. Instalação e Primeiro Servidor

```bash
pip install fastapi uvicorn
```

O `uvicorn` é o servidor ASGI que roda o FastAPI. Pense nele como o equivalente ao servidor interno do Streamlit — você não escreve nada nele, apenas o usa para subir a aplicação.

```python
# main.py — o servidor mais simples possível
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def raiz():
    return {"mensagem": "API de IA funcionando"}
```

```bash
uvicorn main:app --reload
```

Acesse `http://localhost:8000` — você verá o JSON de resposta.
Acesse `http://localhost:8000/docs` — você verá a documentação interativa gerada automaticamente. Esse é o Swagger UI, e ele vai ser o seu melhor aliado para testar endpoints sem precisar de um front-end pronto.

---

# 4. Pydantic — A Validação que Vem de Graça

O FastAPI usa Pydantic para validar dados de entrada e saída. Você define um modelo Python com type hints, e o FastAPI garante que qualquer dado que não bater com esse formato retorna um erro `422` claro para o cliente.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Define o formato esperado do corpo da requisição
class EntradaAnalise(BaseModel):
    texto: str
    idioma: str = "pt"      # valor padrão
    max_tokens: int = 512   # valor padrão

# Define o formato da resposta
class ResultadoAnalise(BaseModel):
    sentimento: str
    confianca: float
    tokens_usados: int

@app.post("/v1/analise/sentimento", response_model=ResultadoAnalise)
def analisar_sentimento(entrada: EntradaAnalise):
    # Aqui entraria a chamada ao modelo real
    # Por enquanto, simulamos a resposta
    return ResultadoAnalise(
        sentimento="negativo" if "defeito" in entrada.texto else "positivo",
        confianca=0.87,
        tokens_usados=len(entrada.texto.split())
    )
```

O que acontece se o cliente enviar dados errados:

```bash
# Enviar um número onde se espera string
curl -X POST http://localhost:8000/v1/analise/sentimento \
  -H "Content-Type: application/json" \
  -d '{"texto": 123}'

# FastAPI responde automaticamente:
# 422 Unprocessable Entity
# {"detail": [{"loc": ["body", "texto"], "msg": "str type expected", ...}]}
```

Esse comportamento é gratuito — você não escreve nenhuma validação manual.

---

# 5. A Conexão com a Aula 06 — O Provider Vira uma Rota

Na Aula 06 construímos esta pilha:

```
UI → Feature → Pipeline → Provider
```

O `provider.py` era o ponto de contato com o modelo ou banco de dados. Ele ficava dentro do mesmo processo do Streamlit. Agora, esse provider se torna uma **rota FastAPI**:

```python
# Antes (semestre 1) — provider.py dentro do Streamlit
# providers/modelo_provider.py
import anthropic

def classificar_texto(texto: str) -> dict:
    client = anthropic.Anthropic()
    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": f"Classifique: {texto}"}]
    )
    return {"resultado": resposta.content[0].text}
```

```python
# Depois (semestre 2) — provider.py vira rota FastAPI
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import anthropic

app = FastAPI(title="API de IA", version="1.0.0")

class EntradaClassificacao(BaseModel):
    texto: str

@app.post("/v1/classificar")
def classificar_texto(entrada: EntradaClassificacao):
    client = anthropic.Anthropic()
    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": f"Classifique: {entrada.texto}"}]
    )
    return {"resultado": resposta.content[0].text}
```

A diferença: agora qualquer cliente (Streamlit, Gradio, app mobile, outro serviço) pode chamar `/v1/classificar` via HTTP. O modelo não está preso a nenhuma interface.

---

# 6. Parâmetros de URL e Query String

Nem tudo vai no corpo da requisição. O FastAPI suporta os três tipos de parâmetros nativamente:

```python
from fastapi import FastAPI
from typing import Optional

app = FastAPI()

# Parâmetro de path — obrigatório, faz parte da URL
@app.get("/v1/analise/{analise_id}")
def buscar_analise(analise_id: int):
    return {"id": analise_id, "texto": "..."}

# Query string — opcional, vem depois do ?
@app.get("/v1/historico")
def listar_historico(pagina: int = 1, tamanho: int = 10, idioma: Optional[str] = None):
    return {"pagina": pagina, "tamanho": tamanho, "idioma": idioma}

# Chamadas correspondentes:
# GET /v1/analise/42
# GET /v1/historico?pagina=2&tamanho=5&idioma=pt
```

---

# 7. Estrutura de Projeto FastAPI

Assim como no Streamlit seguimos Feature-First, o FastAPI também tem suas convenções:

```
meu_projeto/
├── main.py              ← ponto de entrada (cria o app, inclui os routers)
├── routers/
│   ├── analise.py       ← endpoints de /v1/analise/...
│   └── historico.py     ← endpoints de /v1/historico/...
├── models/
│   ├── entrada.py       ← modelos Pydantic de request
│   └── saida.py         ← modelos Pydantic de response
├── providers/
│   └── modelo_provider.py  ← a mesma lógica que estava no Streamlit
└── requirements.txt
```

```python
# main.py com routers
from fastapi import FastAPI
from routers import analise, historico

app = FastAPI(title="API de IA - FIAP", version="1.0.0")

app.include_router(analise.router, prefix="/v1/analise", tags=["Análise"])
app.include_router(historico.router, prefix="/v1/historico", tags=["Histórico"])
```

```python
# routers/analise.py
from fastapi import APIRouter
from models.entrada import EntradaAnalise
from models.saida import ResultadoAnalise
from providers import modelo_provider

router = APIRouter()

@router.post("/sentimento", response_model=ResultadoAnalise)
def analisar_sentimento(entrada: EntradaAnalise):
    return modelo_provider.classificar(entrada.texto)
```

Essa estrutura espelha o Feature-First do semestre 1 — cada router é uma feature do produto.

---

# 8. Rodando Front e Back Juntos

Durante o desenvolvimento você vai ter dois processos rodando ao mesmo tempo:

```bash
# Terminal 1 — back-end
uvicorn main:app --reload --port 8000

# Terminal 2 — front-end
streamlit run app.py
```

O Streamlit na porta `8501` vai chamar o FastAPI na porta `8000`. Na Aula 2 vamos ver como fazer essa chamada de forma correta e robusta.

---

# Referências

- [FastAPI — Documentação Oficial](https://fastapi.tiangolo.com)
- [Pydantic](https://docs.pydantic.dev)
- [Uvicorn](https://www.uvicorn.org)
- [Tiangolo — Sebastian Ramirez (criador do FastAPI)](https://tiangolo.com)
