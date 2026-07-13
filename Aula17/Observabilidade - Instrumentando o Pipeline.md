# Aula 6 — Observabilidade: Instrumentando o Pipeline ao Vivo

## Objetivo

Adicionar instrumentação completa ao pipeline do Sprint e explorar o dashboard do LangSmith com dados reais. Entender o que os traces revelam sobre o comportamento do modelo e como usar esse conhecimento para melhorar o produto.

---

# 1. Revisão — O que Configuramos na Aula Anterior

Na Aula 5 configuramos o ambiente e fizemos a primeira chamada traceable. Agora vamos ir além: instrumentar cada camada do pipeline, não apenas o provider.

```
Pipeline atual (Aula 5)
app.py → pipeline.py → provider.py  ← @traceable aqui

Pipeline desta aula
app.py → pipeline.py ← @traceable aqui
              └─ provider.py ← @traceable aqui
```

Quando cada camada tem seu próprio trace, o LangSmith monta uma árvore hierárquica — você vê não só o tempo total, mas onde especificamente o pipeline é lento.

---

# 2. Instrumentando o Pipeline Completo

```python
# backend/pipelines/news_pipeline.py
from langsmith import traceable
from providers import scraper_nlp_provider, modelo_provider

@traceable(name="pipeline_noticia", tags=["producao", "v1"])
def processar_noticia(url: str = None, texto: str = None, session_id: str = None) -> dict:
    """
    Pipeline completo: scraping → NLP → modelo.
    Cada etapa tem seu próprio trace filho.
    """
    # Etapa 1 — Obter o texto
    conteudo = _obter_conteudo(url=url, texto=texto, session_id=session_id)
    if not conteudo:
        return {"erro": "Não foi possível obter o conteúdo."}

    # Etapa 2 — Extrair entidades e pré-processar
    entidades = _extrair_entidades(conteudo, session_id=session_id)

    # Etapa 3 — Analisar com modelo
    analise = modelo_provider.analisar_completo(conteudo, entidades, session_id=session_id)

    return {
        "resumo": analise["resumo"],
        "sentimento": analise["sentimento"],
        "entidades": entidades,
        "confianca": analise["confianca"],
        "tokens_usados": analise["tokens_usados"]
    }

@traceable(name="obter_conteudo")
def _obter_conteudo(url: str = None, texto: str = None, session_id: str = None) -> str | None:
    if texto:
        return texto
    if url:
        return scraper_nlp_provider.raspar_url(url)
    return None

@traceable(name="extrair_entidades")
def _extrair_entidades(texto: str, session_id: str = None) -> list[str]:
    return scraper_nlp_provider.extrair_entidades(texto)
```

```python
# backend/providers/modelo_provider.py
import anthropic
from langsmith import traceable

client = anthropic.Anthropic()

@traceable(name="modelo_analisar_completo", metadata={"modelo": "claude-haiku-4-5-20251001"})
def analisar_completo(texto: str, entidades: list[str], session_id: str = None) -> dict:
    """
    Chama o modelo para resumo + sentimento em uma única chamada.
    metadata= adiciona informações fixas ao trace para filtragem no dashboard.
    """
    prompt = f"""Analise a notícia abaixo e retorne um JSON com:
- resumo: resumo em 2 frases
- sentimento: "positivo", "negativo" ou "neutro"
- confianca: score de 0.0 a 1.0

Entidades identificadas: {', '.join(entidades)}

Notícia:
{texto[:2000]}

Retorne apenas o JSON, sem explicações."""

    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    conteudo = resposta.content[0].text.strip()

    try:
        resultado = json.loads(conteudo)
    except json.JSONDecodeError:
        # Modelo retornou algo fora do formato esperado — registramos isso
        resultado = {"resumo": conteudo, "sentimento": "indefinido", "confianca": 0.0}

    resultado["tokens_usados"] = resposta.usage.input_tokens + resposta.usage.output_tokens
    return resultado
```

---

# 3. Propagando o ID de Sessão

Para conectar os traces do LangSmith com as sessões do front-end, precisamos propagar o `session_id` do header HTTP até o provider.

```python
# backend/routers/noticias.py
from fastapi import APIRouter, Security, Header
from typing import Optional

router = APIRouter()

@router.post("/noticias/analisar")
def analisar_noticia(
    entrada: EntradaNoticia,
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),  # lê o header X-Session-Id
    x_feature: Optional[str] = Header(None)
):
    # Passa o session_id para o pipeline, que passa para os providers
    resultado = news_pipeline.processar_noticia(
        url=entrada.url,
        texto=entrada.texto,
        session_id=x_session_id
    )
    return resultado
```

No LangSmith, você pode filtrar todos os traces de uma sessão específica e reconstruir exatamente o que um usuário fez durante sua visita ao app.

---

# 4. Lendo o Dashboard ao Vivo

Acesse `https://smith.langchain.com/o/seu-org/projects/p/sprint-fiap`.

**O que observar primeiro:**

**Latência por etapa**
O gráfico de cascata mostra cada `@traceable` como uma barra. Se `extrair_entidades` demora 3s e `modelo_analisar_completo` demora 0.8s, o gargalo está no scraping/NLP, não no modelo. Isso direciona onde otimizar.

**Tokens e custo**
O LangSmith acumula tokens usados por projeto e estima o custo. Você visualiza qual combinação de prompt + modelo é mais eficiente — um prompt mais curto pode custar metade e dar o mesmo resultado.

**Taxa de erro**
Tracesss com exceção aparecem em vermelho. O LangSmith mostra o stack trace completo — você vê exatamente onde o pipeline quebrou e com qual input.

**Distribuição de sentimentos**
Com dados reais, você começa a ver padrões: 70% das análises retornam "negativo"? Pode ser viés do dataset de treino, pode ser um problema no prompt.

---

# 5. Adicionando Tags e Metadados

Tags e metadados tornam o dashboard filtrável e útil para comparação de versões:

```python
from langsmith import traceable

# Tags: rótulos livres para filtrar no dashboard
@traceable(
    name="analisar_sentimento",
    tags=["producao", "v2", "noticias"]
)
def analisar(texto: str) -> dict:
    ...

# run_metadata: dicionário com informações contextuais
@traceable(
    name="pipeline_principal",
    metadata={
        "modelo": "claude-haiku-4-5-20251001",
        "idioma": "pt",
        "feature": "news-analysis",
        "versao_prompt": "v3"
    }
)
def pipeline(texto: str) -> dict:
    ...
```

Quando você atualiza o prompt (de `versao_prompt: v2` para `v3`), filtra no LangSmith e compara as métricas lado a lado — latência, tokens, qualidade das respostas.

---

# 6. Enviando Feedback do Front-end

O like/dislike que construímos no Gradio na Aula 09 do semestre 1 pode alimentar o LangSmith. Para isso, o back-end precisa retornar o `run_id` do trace junto com a resposta:

```python
# backend/routers/noticias.py
from langsmith import get_current_run_tree

@router.post("/noticias/analisar")
def analisar_noticia(entrada: EntradaNoticia, ...):
    resultado = news_pipeline.processar_noticia(...)

    # Captura o ID do trace atual para retornar ao front-end
    run_tree = get_current_run_tree()
    run_id = str(run_tree.id) if run_tree else None

    return {**resultado, "trace_id": run_id}
```

```python
# backend/routers/feedback.py
from fastapi import APIRouter
from pydantic import BaseModel
from langsmith import Client

router = APIRouter()
ls_client = Client()

class EntradaFeedback(BaseModel):
    trace_id: str
    aprovado: bool
    comentario: str | None = None

@router.post("/feedback")
def registrar_feedback(feedback: EntradaFeedback, _: str = Security(verificar_chave)):
    ls_client.create_feedback(
        run_id=feedback.trace_id,
        key="aprovacao_usuario",
        score=1.0 if feedback.aprovado else 0.0,
        comment=feedback.comentario
    )
    return {"status": "registrado"}
```

```python
# frontend — enviando feedback após o resultado
import requests

def enviar_feedback(trace_id: str, aprovado: bool):
    requests.post(
        f"{API_URL}/v1/feedback",
        json={"trace_id": trace_id, "aprovado": aprovado},
        headers=_HEADERS
    )

# Após exibir o resultado
if resultado and resultado.get("trace_id"):
    col1, col2 = st.columns(2)
    if col1.button("👍 Útil"):
        enviar_feedback(resultado["trace_id"], aprovado=True)
        st.toast("Obrigado pelo feedback!")
    if col2.button("👎 Não útil"):
        enviar_feedback(resultado["trace_id"], aprovado=False)
        st.toast("Feedback registrado.")
```

Com isso, cada like/dislike do usuário fica associado ao trace exato do modelo — você sabe qual resposta agradou e qual não agradou, e pode usar esses dados para melhorar o prompt.

---

# 7. Alternativa — Arize Phoenix (self-hosted)

Para quem prefere não enviar dados para um serviço externo, o Arize Phoenix oferece as mesmas capacidades rodando localmente:

```bash
pip install arize-phoenix
python -m phoenix.server.main
# Interface em http://localhost:6006
```

```python
import phoenix as px
from openinference.instrumentation.anthropic import AnthropicInstrumentor

px.launch_app()
AnthropicInstrumentor().instrument()

# A partir daqui, todas as chamadas Anthropic são capturadas automaticamente
```

A escolha entre LangSmith (cloud) e Phoenix (self-hosted) depende de requisitos de privacidade dos dados. Em produção com dados sensíveis, Phoenix é a escolha mais segura.

---

# Referências

- [LangSmith — Tracing](https://docs.smith.langchain.com/observability/how_to_guides/tracing)
- [LangSmith — Feedback](https://docs.smith.langchain.com/evaluation/how_to_guides/annotation_queues)
- [Arize Phoenix](https://docs.arize.com/phoenix)
- [OpenTelemetry — Semantic Conventions for AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
