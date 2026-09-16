# Aula 17 — Observabilidade: Instrumentando o que Já Existe no Forzy

## Objetivo

Aplicar o LangSmith nas funções que **já existem** no Forzy: `@traceable` não sabe nem se importa se a função por trás dele chama um LLM ou só faz uma query SQLite — ele observa qualquer função Python. Vamos instrumentar `equipamento_provider`, `sensor_provider` e `planta_provider`, ver as árvores de trace no dashboard, e enriquecer tudo isso com headers adicionais que o front-end (Gradio) passa a mandar.

---

# 1. Por que Observar Algo que Não Tem IA

**Qualquer** camada de acesso a dados pode estar tecnicamente saudável (sem exceção, `200 OK`) e ainda assim esconder informação importante — quanto tempo uma consulta no `motor.db` realmente levou, com que TAG um endpoint foi chamado, se a severidade calculada bateu com o que o front-end mostrou. Hoje, se um aluno reclamar "o dashboard demorou pra carregar", a única forma de investigar é adicionar `print()` manualmente e reproduzir o problema. Com tracing, isso já está registrado.

Vamos tratar cada request ao back-end do Forzy como um pipeline observável, do mesmo jeito que trataríamos uma chamada a um modelo — só que aqui as etapas são `router → provider → SQLite`, sem nenhum LLM no meio.

---

# 2. Instrumentando os `providers/` — a camada de dados

Nenhuma lógica muda. Só entra o decorator.

```python
# backend/providers/equipamento_provider.py
from langsmith import traceable

# ... imports e _conn(), _row_to_dict() continuam idênticos à Aula 15 ...

@traceable(name="db_listar_equipamentos", run_type="tool", tags=["forzy", "sqlite", "equipamentos"])
def listar_todos() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM motores ORDER BY motor_id").fetchall()
    return [_row_to_dict(r) for r in rows]


@traceable(name="db_buscar_equipamento", run_type="tool", tags=["forzy", "sqlite", "equipamentos"])
def buscar_por_tag(tag: str) -> Optional[dict]:
    try:
        mid = int(tag.strip().upper().replace("MTR-", ""))
    except (ValueError, AttributeError):
        return None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM motores WHERE motor_id = ?", (mid,)).fetchone()
    return _row_to_dict(row) if row else None


@traceable(name="db_salvar_equipamento", run_type="tool", tags=["forzy", "sqlite", "equipamentos"])
def salvar(dados: dict) -> tuple[bool, str]:
    # corpo idêntico ao da Aula 15 — só o decorator foi acrescentado
    ...
```

`run_type="tool"` (em vez de `"llm"` ou `"chain"`) é a marcação correta para "isto é uma chamada auxiliar de dados, não uma etapa de orquestração nem um modelo" — o LangSmith usa esse tipo para agrupar visualmente esse tipo de run no dashboard.

O mesmo padrão se aplica aos outros dois providers:

```python
# backend/providers/sensor_provider.py
from langsmith import traceable

@traceable(name="db_leitura_atual", run_type="tool", tags=["forzy", "sqlite", "sensores"])
def leitura_atual(tag: str) -> dict:
    ...  # idêntico à Aula 15


@traceable(name="db_historico", run_type="tool", tags=["forzy", "sqlite", "sensores"])
def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    ...  # idêntico à Aula 15
```

```python
# backend/providers/planta_provider.py
from langsmith import traceable

@traceable(name="hierarquia_listar_plantas", run_type="tool", tags=["forzy", "plantas"])
def listar_plantas() -> list[str]:
    return sorted(_HIERARQUIA.keys())


@traceable(name="hierarquia_buscar_localizacao", run_type="tool", tags=["forzy", "plantas"])
def buscar_localizacao(tag: str) -> tuple[str, str]:
    ...  # idêntico à Aula 15
```

Repare: mesmo sendo um dicionário em memória (sem I/O nenhum), vale a pena instrumentar `planta_provider` — no dashboard, ele deve aparecer com latência praticamente zero, o que serve de referência de comparação com os providers que batem no SQLite.

---

# 3. Instrumentando a Regra de Negócio — `_com_severidade`

A classificação ISO 10816 em `backend/routers/sensores.py` é a única lógica de decisão do projeto (fora do CRUD puro) — vale a pena observá-la separadamente, porque é o tipo de coisa que muda com frequência (limites podem ser recalibrados) e cujo comportamento você quer conseguir auditar:

```python
# backend/routers/sensores.py
from langsmith import traceable

_LIMITES = {
    "temp_c":       {"aviso": 75,  "critico": 90},
    "vibracao_mms": {"aviso": 4.5, "critico": 7.1},
}


def _severidade(chave: str, valor: float) -> str:
    limites = _LIMITES.get(chave)
    if not limites:
        return "normal"
    if valor >= limites["critico"]:
        return "critico"
    if valor >= limites["aviso"]:
        return "aviso"
    return "normal"


@traceable(name="classificar_severidade", run_type="tool", tags=["forzy", "iso10816"])
def _com_severidade(leitura: dict) -> dict:
    resultado = {
        **leitura,
        "severidade_temp":     _severidade("temp_c", leitura["temp_c"]),
        "severidade_vibracao": _severidade("vibracao_mms", leitura["vibracao_mms"]),
    }
    return resultado
```

Com isso instrumentado, dá pra filtrar no LangSmith só os runs de `classificar_severidade` e ver, por exemplo, que porcentagem das leituras dos últimos 7 dias caiu em `"critico"` — sem precisar tocar no banco.

---

# 4. Instrumentando o Endpoint — o Run "Pai" de Cada Request

Os providers acima, sozinhos, geram traces soltos e desconexos — um por chamada, sem hierarquia. Para que o LangSmith monte a árvore completa de um request (endpoint → provider → SQLite), o próprio handler do FastAPI vira o run pai. Como decorar diretamente a função de rota pode interferir na injeção de dependências do FastAPI (`Security`, `Header`), usamos o context manager `trace()` dentro do corpo da função, em vez do decorator `@traceable`:

```python
# backend/routers/sensores.py
from typing import Optional
from fastapi import APIRouter, Security, Header
from langsmith import trace

from auth.seguranca import verificar_chave
from models.saida import LeituraSaida
import providers.sensor_provider as sensor_provider

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("/{tag}/leitura-atual", response_model=LeituraSaida)
def leitura_atual(
    tag: str,
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_app_version: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
    x_client_platform: Optional[str] = Header(None),
):
    with trace(
        name="endpoint_leitura_atual",
        run_type="chain",
        tags=["forzy", "sensores", "endpoint"],
        metadata={
            "tag": tag,
            "session_id": x_session_id,
            "app_version": x_app_version,
            "feature": x_feature,
            "client_platform": x_client_platform,
        },
    ):
        leitura = sensor_provider.leitura_atual(tag)   # já é @traceable — vira run filho automaticamente
        return _com_severidade(leitura)                 # já é @traceable — outro run filho
```

O `with trace(...)` cria o run pai e, como o LangSmith propaga contexto via `contextvars`, qualquer função `@traceable` chamada dentro do bloco (`sensor_provider.leitura_atual`, `_com_severidade`) é automaticamente encaixada como filha desse run — sem passar nenhum id manualmente. O mesmo padrão se replica nos outros endpoints:

```python
# backend/routers/equipamentos.py
@router.get("", response_model=list[EquipamentoSaida])
def listar_equipamentos(
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
):
    with trace(
        name="endpoint_listar_equipamentos",
        run_type="chain",
        tags=["forzy", "equipamentos", "endpoint"],
        metadata={"session_id": x_session_id, "feature": x_feature},
    ):
        return eq_provider.listar_todos()
```

```python
# backend/routers/plantas.py
@router.get("/{planta}/areas/{area}/equipamentos", response_model=list[str])
def listar_equipamentos_area(
    planta: str,
    area: str,
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
):
    with trace(
        name="endpoint_listar_equipamentos_area",
        run_type="chain",
        tags=["forzy", "plantas", "endpoint"],
        metadata={"planta": planta, "area": area, "session_id": x_session_id, "feature": x_feature},
    ):
        return planta_provider.listar_equipamentos(planta, area)
```

---

# 5. Headers Novos: o que o Front-end Passa a Mandar

Até então o `api_provider.py` só mandava `X-API-Key`. Agora ele passa a enviar quatro headers a mais, sempre — são eles que alimentam o `metadata` mostrado acima:

| Header | Preenchido com | Aparece no LangSmith como |
|---|---|---|
| `X-Session-Id` | UUID gerado uma vez por processo Gradio | `metadata.session_id` — permite reconstruir tudo que uma sessão fez |
| `X-App-Version` | Versão fixa do front (`"1.3.0"`) | `metadata.app_version` — compara comportamento entre versões após um deploy |
| `X-Feature` | Nome da página/feature que originou a chamada (`"dashboard"`, `"sensores"`, `"cadastro"`) | `metadata.feature` — filtra o dashboard por área do app, sem abrir trace por trace |
| `X-Client-Platform` | Fixo (`"gradio-desktop"`) | `metadata.client_platform` — útil no dia em que existir um segundo cliente (mobile, CLI) |

```python
# frontend/providers/api_provider.py
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "chave-local-dev")
APP_VERSION = os.getenv("APP_VERSION", "1.3.0")

_SESSION_ID = str(uuid.uuid4())  # um por processo — poderia ser por aba, se o Gradio suportar
_TIMEOUT = 10


def _headers(feature: str) -> dict:
    return {
        "X-API-Key": API_KEY,
        "X-Session-Id": _SESSION_ID,
        "X-App-Version": APP_VERSION,
        "X-Feature": feature,
        "X-Client-Platform": "gradio-desktop",
    }


def _get(path: str, feature: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_headers(feature), params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        print(f"[api_provider] Não foi possível conectar ao back-end em {API_URL}.")
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        print(f"[api_provider] Erro {e.response.status_code} em {path}: {e.response.text}")
        return None


# cada chamada agora identifica de qual feature ela vem
def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos", feature="equipamentos") or []


def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual", feature="sensores") or {}


def listar_equipamentos(planta: str, area: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos", feature="dashboard") or []
```

Note que `feature` passa a ser um parâmetro explícito de cada função do `api_provider` — é assim que o front "sabe" de onde a chamada partiu e consegue rotular o header corretamente, sem precisar inspecionar de onde a função foi chamada.

---

# 6. Lendo o Dashboard

Com tudo isso no ar:

**Árvore por request.** Cada chamada ao endpoint de leitura aparece como `endpoint_leitura_atual` com dois filhos: `db_leitura_atual` (a query) e `classificar_severidade` (a regra). Dá pra ver exatamente quanto do tempo total foi SQLite e quanto foi Python puro.

**Filtro por feature.** Como `metadata.feature` está presente em todo trace, filtrar `feature = "dashboard"` isola só os requests originados da navegação Planta → Área → Equipamento, sem misturar com a página de Sensores.

**Filtro por sessão.** `metadata.session_id` permite pegar uma sessão específica do Gradio e ver, em ordem, tudo que aquele processo fez — útil se alguém reportar "o app ficou lento" e você quiser reconstruir o que aconteceu antes.

**Comparação entre versões.** Se `APP_VERSION` mudar de `"1.3.0"` para `"1.4.0"` num deploy, filtrar por `metadata.app_version` e comparar latência/erro entre as duas versões mostra se o deploy piorou algo, sem precisar de nenhuma ferramenta de deploy adicional.

**Taxa de erro por camada.** Um trace vermelho em `db_buscar_equipamento` (TAG inexistente) é visualmente diferente de um erro em `endpoint_leitura_atual` propagado de mais fundo — a árvore já mostra em qual camada a exceção nasceu.

---

# 7. Alternativa — Arize Phoenix em Detalhe

## 7.1 O que é

Arize Phoenix é a ferramenta de observabilidade **open-source** da Arize AI, construída em cima do **OpenTelemetry** — o padrão vendor-neutral de telemetria distribuída. A diferença central em relação ao LangSmith não é a funcionalidade, é onde os dados moram: Phoenix roda **localmente ou em infraestrutura própria** (self-hosted), então nada do que passa pelo Forzy — TAGs de motores, leituras, dados de planta — sai da rede da empresa. Para um sistema industrial como este, cujos dados podem ser proprietários de uma planta específica, isso pesa mais do que pesaria num app de uso geral.

## 7.2 Hierarquia de conceitos

| LangSmith | Phoenix / OpenTelemetry |
|---|---|
| Project | Project |
| Trace | Trace |
| Run | Span |
| `tags=[...]` | atributos de span (`span.set_attribute`) |
| `metadata={...}` | atributos de span |
| `run_type="tool"` | atributo customizado (ex: `span.kind = "TOOL"`) |

## 7.3 Instrumentação equivalente

```python
# backend/providers/equipamento_provider.py — versão Phoenix
from opentelemetry import trace as otel_trace

tracer = otel_trace.get_tracer(__name__)


def listar_todos() -> list[dict]:
    with tracer.start_as_current_span("db_listar_equipamentos") as span:
        span.set_attribute("forzy.camada", "sqlite")
        with _conn() as conn:
            rows = conn.execute("SELECT * FROM motores ORDER BY motor_id").fetchall()
        resultado = [_row_to_dict(r) for r in rows]
        span.set_attribute("forzy.total_registros", len(resultado))
        return resultado
```

```python
# backend/routers/sensores.py — versão Phoenix, com os mesmos headers da seção 5
@router.get("/{tag}/leitura-atual", response_model=LeituraSaida)
def leitura_atual(
    tag: str,
    _: str = Security(verificar_chave),
    x_session_id: Optional[str] = Header(None),
    x_app_version: Optional[str] = Header(None),
    x_feature: Optional[str] = Header(None),
):
    with tracer.start_as_current_span("endpoint_leitura_atual") as span:
        span.set_attribute("forzy.tag", tag)
        span.set_attribute("session.id", x_session_id or "desconhecida")
        span.set_attribute("app.version", x_app_version or "desconhecida")
        span.set_attribute("forzy.feature", x_feature or "desconhecida")

        leitura = sensor_provider.leitura_atual(tag)      # span filho automático (contextvars do OTel)
        return _com_severidade(leitura)                    # span filho automático
```

```python
# backend/main.py — inicialização, uma vez, no startup
from phoenix.otel import register

register(project_name="forzy-digital-twin", endpoint="http://localhost:6006/v1/traces")
```

## 7.4 O que muda para migrar

| Item | LangSmith | Phoenix |
|---|---|---|
| Onde os dados ficam | Cloud (`smith.langchain.com`) | Local — `python -m phoenix.server.main`, porta `6006` |
| Dependências | `langsmith` | `arize-phoenix`, `opentelemetry-sdk` |
| Variáveis de ambiente | `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_TRACING` | Nenhuma API key — só o `endpoint` do coletor local |
| Instrumentar providers | `@traceable(run_type="tool")` na função | `with tracer.start_as_current_span(...)` envolvendo o corpo |
| Instrumentar endpoints | `with trace(...)` do LangSmith | `with tracer.start_as_current_span(...)` do OpenTelemetry |
| Passar headers como metadata | `metadata={...}` no `trace()` | `span.set_attribute(...)` |
| Hierarquia pai-filho | Automática via `contextvars` do LangSmith | Automática via `contextvars` do OpenTelemetry — mesmo mecanismo |
| Dashboard | `smith.langchain.com` | `http://localhost:6006` |

```bash
# backend/requirements.txt — trocando LangSmith por Phoenix
arize-phoenix>=5.0.0
opentelemetry-sdk>=1.24.0
```

```bash
# rodar o coletor localmente (processo separado, terceiro terminal)
python -m phoenix.server.main serve
```

## 7.5 Uma ressalva importante sobre Phoenix para casos sem IA

O dashboard do Phoenix foi desenhado em torno de convenções semânticas de LLM (prompt, completion, tokens) — spans genéricos de negócio, como os do Forzy, aparecem e funcionam normalmente (afinal, é OpenTelemetry puro por baixo), mas a visualização é menos rica para esse caso do que seria para um span de chamada a modelo. Se o objetivo fosse observar **só** lógica de negócio sem nenhuma IA no projeto, vale considerar um backend de OpenTelemetry mais genérico (Jaeger, Grafana Tempo) em vez de Phoenix.

## 7.6 Quando escolher qual

Phoenix compensa quando os dados do Forzy são proprietários e não podem sair da rede do cliente, ou quando o time já usa OpenTelemetry em outros serviços e quer um único padrão. LangSmith compensa quando o time quer o menor esforço de instrumentação possível e não tem infraestrutura própria para hospedar um dashboard adicional.

---

# Referências

- [LangSmith — Tracing Quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- [LangSmith — `trace()` context manager](https://docs.smith.langchain.com/observability/how_to_guides/tracing)
- [Arize Phoenix — Documentação](https://docs.arize.com/phoenix)
- [Arize Phoenix — Quickstart Tracing](https://docs.arize.com/phoenix/tracing/llm-traces)
- [OpenTelemetry — Python SDK](https://opentelemetry.io/docs/languages/python/)
- [ISO 10816 — Mechanical vibration evaluation](https://www.iso.org/standard/23076.html)
