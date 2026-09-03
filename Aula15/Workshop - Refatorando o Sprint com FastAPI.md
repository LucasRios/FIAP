## Objetivo

Pegar o projeto real do Sprint — **Forzy · Digital Twin**, um app Gradio que lê e grava dados de motores industriais direto num banco SQLite — e separar essa lógica em um back-end FastAPI de verdade. O front-end (Gradio) deixa de acessar banco de dados e passa a consumir tudo via HTTP. Aplicamos segurança real com variáveis de ambiente e proteção de rotas por API Key.

Esta aula é densa de propósito — o conteúdo deve render mais de um encontro. 

---

# 1. O Ponto de Partida — a arquitetura real do Sprint

O projeto que vocês têm em mãos (pasta `sprint_antiga/`) é este:

```
app.py (Gradio)
 ├─ ui/sidebar.py            ← menu lateral (Equipamentos, Dados de Sensores, Dashboard)
 ├─ state/app_state.py       ← gr.State compartilhados entre páginas
 │
 ├─ features/equipamentos/page.py   ← lista de motores cadastrados
 ├─ features/cadastro/page.py       ← formulário técnico (criar/editar motor)
 ├─ features/sensores/page.py       ← leitura atual + histórico 24h
 ├─ features/dashboard/page.py      ← navegação Planta→Área→Equipamento + gráficos
 │
 ├─ pipelines/cadastro_pipeline.py   ← formata dados de equipamento p/ Gradio
 ├─ pipelines/sensor_pipeline.py     ← classifica severidade + formata leituras
 ├─ pipelines/dashboard_pipeline.py  ← monta cards, gráficos Plotly e placa técnica
 │
 └─ providers/equipamento_provider.py  ← acessa motor.db (SQLite) DIRETO
    providers/sensor_provider.py       ← acessa motor.db (SQLite) DIRETO
    providers/planta_provider.py       ← acessa hierarquia Planta→Área→TAG (em memória)
```

Os três `providers/*.py` fazem o que pertence ao back-end:

1. `equipamento_provider.py` — abre conexão SQLite (`motor.db`), lê/grava a tabela `motores`, valida cadastro (upsert).
2. `sensor_provider.py` — lê a tabela `leituras` do mesmo banco, converte grandezas físicas.
3. `planta_provider.py` — conhece a hierarquia física da planta industrial (Planta → Área → TAG).

O Gradio executa tudo isso **dentro do próprio processo**. Isso significa:
- Se dois usuários acessarem o app ao mesmo tempo, os dois processos abrem conexões SQLite concorrentes no mesmo arquivo, dentro do mesmo servidor Gradio, competindo por I/O.
- Não existe nenhuma proteção — qualquer pessoa que rode `app.py` lê e grava o banco de motores sem autenticação.
- A lógica de negócio (regras de severidade ISO 10816, validação de TAG, upsert) está amarrada ao Gradio e não pode ser reaproveitada por nenhum outro cliente (um app mobile, um script de outro time, etc.).

---

# 2. O Que Vamos Mudar

```
# Antes — tudo junto, um único processo
Gradio → pipeline → provider → SQLite (motor.db) / dict em memória (planta_provider)

# Depois — separado, dois processos
Gradio → api_provider → [HTTP + API Key] → FastAPI → providers → SQLite (motor.db)
```

A regra que guia a refatoração continua a mesma:

> **Se a lógica não é sobre exibir ou coletar dados do usuário, ela pertence ao back-end.**

Aplicando a regra aos arquivos reais do Sprint:

| Arquivo atual | Fica no back-end? | Por quê |
|---|---|---|
| `providers/equipamento_provider.py` | ✅ Sim | Acessa banco de dados — nunca deveria estar no processo do Gradio |
| `providers/sensor_provider.py` | ✅ Sim | Acessa banco de dados |
| `providers/planta_provider.py` | ✅ Sim | É a fonte de verdade da hierarquia física do ativo |
| Classificação de severidade (`_severidade`, limites ISO 10816) | ✅ Sim | É regra de negócio, não é sobre exibir dados |
| `pipelines/cadastro_pipeline.py` (formatar tabela, montar ficha em Markdown) | ⬜ Não — fica no front | Formata dado *para o componente Gradio* específico |
| `pipelines/sensor_pipeline.py` (montar Markdown/Dataframe) | ⬜ Não — fica no front | Mesma razão |
| `pipelines/dashboard_pipeline.py` (montar Plotly, cards, placa) | ⬜ Não — fica no front | Mesma razão — é 100% apresentação visual |
| `features/*/page.py`, `ui/sidebar.py`, `state/app_state.py`, `app.py` | ⬜ Não — fica no front | É a UI em si |

Ou seja: **os três `providers/` migram inteiros para o back-end**. As `pipelines/` continuam no front-end, mas param de importar os providers antigos e passam a chamar um novo `providers/api_provider.py`, que faz requisições HTTP para o FastAPI. Como o `api_provider` vai expor exatamente as mesmas funções que os providers antigos tinham, **as pipelines quase não mudam** — só a linha de `import`.

---

# PARTE 1 — BACK-END (FastAPI)

Vamos construir o back-end seguindo esta estrutura:

```
backend/
├── main.py                      ← ponto de entrada (cria o app, inclui os routers)
├── auth/
│   └── seguranca.py             ← autenticador de API Key
├── routers/
│   ├── equipamentos.py          ← endpoints de /v1/equipamentos/...
│   ├── plantas.py               ← endpoints de /v1/plantas/...
│   └── sensores.py              ← endpoints de /v1/sensores/...
├── models/
│   ├── entrada.py                ← modelos Pydantic de request
│   └── saida.py                  ← modelos Pydantic de response
├── providers/
│   ├── equipamento_provider.py   ← copiado do Sprint, sem alteração de lógica
│   ├── planta_provider.py        ← copiado do Sprint, sem alteração de lógica
│   └── sensor_provider.py        ← copiado do Sprint, sem alteração de lógica
├── motor.db                       ← movido para cá (era sprint_antiga/providers/motor.db)
├── .env
└── requirements.txt
```

O princípio: **os providers não mudam de lógica, só de endereço.** Eles já estavam corretos (SQLite, upsert, hierarquia) — o problema era só onde rodavam.

## 1.1 `providers/` — copiados sem alteração de lógica

Copie os três arquivos de `sprint_antiga/providers/` para `backend/providers/`, mantendo o conteúdo idêntico. Nenhuma linha de SQL ou de regra de negócio muda. A única coisa que muda é o caminho do banco:

```python
# backend/providers/equipamento_provider.py
# (idêntico ao original — só reforçando o caminho do banco)

import os
import sqlite3
from datetime import datetime
from typing import Optional

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "motor.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _row_to_dict(row: sqlite3.Row) -> dict:
    mid = row["motor_id"]
    pkw = row["potencia_kw"]
    return {
        "tag":                f"MTR-{mid:03d}",
        "modelo":             row["modelo"],
        "fabricante":         row["fabricante"],
        "potencia_cv":        round(pkw * 1.34102, 1),
        "tensao_v":           380,
        "corrente_nominal_a": round(pkw * 1.77, 1),
        "rotacao_rpm":        1760,
        "fator_potencia":     0.86,
        "classe_isolamento":  "F",
        "ip":                 "IP55",
        "peso_kg":            0.0,
        "local":              "",
        "status":             "Operacional",
        "cadastrado_em":      str(row["ano_instalacao"]),
    }


def listar_todos() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM motores ORDER BY motor_id").fetchall()
    return [_row_to_dict(r) for r in rows]


def buscar_por_tag(tag: str) -> Optional[dict]:
    try:
        mid = int(tag.strip().upper().replace("MTR-", ""))
    except (ValueError, AttributeError):
        return None
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM motores WHERE motor_id = ?", (mid,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def salvar(dados: dict) -> tuple[bool, str]:
    tag = dados.get("tag", "").strip().upper()
    if not tag:
        return False, "TAG de identificação é obrigatória."
    if not dados.get("modelo", "").strip():
        return False, "Modelo do equipamento é obrigatório."
    if not dados.get("fabricante", "").strip():
        return False, "Fabricante é obrigatório."

    try:
        mid = int(tag.replace("MTR-", ""))
    except ValueError:
        return False, f"TAG inválida: {tag}. Use o formato MTR-NNN."

    potencia_kw = round((dados.get("potencia_cv") or 0) / 1.34102, 2)

    with _conn() as conn:
        existing = conn.execute(
            "SELECT ano_instalacao FROM motores WHERE motor_id = ?", (mid,)
        ).fetchone()
        eh_novo = existing is None
        ano = datetime.now().year if eh_novo else existing["ano_instalacao"]

        conn.execute(
            """INSERT OR REPLACE INTO motores
               (motor_id, fabricante, modelo, potencia_kw, ano_instalacao)
               VALUES (?, ?, ?, ?, ?)""",
            (mid, dados["fabricante"], dados["modelo"], potencia_kw, ano),
        )

    acao = "cadastrado" if eh_novo else "atualizado"
    return True, f"Equipamento {tag} {acao} com sucesso."


def tags_disponiveis() -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT motor_id FROM motores ORDER BY motor_id"
        ).fetchall()
    return [f"MTR-{r['motor_id']:03d}" for r in rows]
```

```python
# backend/providers/planta_provider.py — idêntico ao original

_HIERARQUIA: dict[str, dict[str, list[str]]] = {
    "Planta A": {
        "Linha 1": ["MTR-001", "MTR-002", "MTR-003", "MTR-004", "MTR-005"],
        "Linha 2": ["MTR-006", "MTR-007", "MTR-008", "MTR-009", "MTR-010"],
    },
    "Planta B": {
        "Utilidades":   ["MTR-011", "MTR-012", "MTR-013", "MTR-014", "MTR-015"],
        "Compressores": ["MTR-016", "MTR-017", "MTR-018", "MTR-019", "MTR-020"],
    },
}


def listar_plantas() -> list[str]:
    return sorted(_HIERARQUIA.keys())


def listar_areas(planta: str) -> list[str]:
    if not planta or planta not in _HIERARQUIA:
        return []
    return sorted(_HIERARQUIA[planta].keys())


def listar_equipamentos(planta: str, area: str) -> list[str]:
    if not planta or not area:
        return []
    return _HIERARQUIA.get(planta, {}).get(area, [])


def buscar_localizacao(tag: str) -> tuple[str, str]:
    for planta, areas in _HIERARQUIA.items():
        for area, equips in areas.items():
            if tag in equips:
                return planta, area
    return "", ""
```

```python
# backend/providers/sensor_provider.py — idêntico ao original

import os
import sqlite3
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "motor.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _tag_to_motor_id(tag: str) -> int:
    try:
        return int(tag.strip().upper().replace("MTR-", ""))
    except (ValueError, AttributeError):
        return 1


def _row_to_leitura(row: sqlite3.Row, tag: str) -> dict:
    return {
        "tag":          tag,
        "timestamp":    row["timestamp"],
        "tensao_v":     380.0,
        "corrente_a":   round(row["corrente_a"],   2),
        "temp_c":       round(row["temperatura_c"], 2),
        "vibracao_mms": round(row["vibracao_mm_s"], 3),
        "rotacao_rpm":  round(row["rotacao_rpm"],   2),
        "falha":        row["falha"],
    }


def leitura_atual(tag: str) -> dict:
    mid = _tag_to_motor_id(tag)
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM leituras WHERE motor_id = ? ORDER BY timestamp DESC LIMIT 1",
            (mid,),
        ).fetchone()
    if row:
        return _row_to_leitura(row, tag)
    return {
        "tag": tag,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tensao_v": 380.0, "corrente_a": 0.0, "temp_c": 0.0,
        "vibracao_mms": 0.0, "rotacao_rpm": 0.0, "falha": 0,
    }


def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    mid = _tag_to_motor_id(tag)
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leituras WHERE motor_id = ? ORDER BY timestamp DESC LIMIT ?",
            (mid, n_pontos),
        ).fetchall()
    return [_row_to_leitura(r, tag) for r in reversed(rows)]
```

> **Nota:** o parâmetro `status` que existia em `leitura_atual(tag, status)` e `historico_simulado(tag, status)` foi removido — ele já não era usado (era vestígio da versão simulada por perfis). Como o resto do sistema depende de dados reais do banco, simplificamos a assinatura.

## 1.2 `models/` — contratos de entrada e saída

Separar `entrada.py` (o que o cliente manda) de `saida.py` (o que a API devolve) deixa explícito o contrato da API e evita confundir os dois lados.

```python
# backend/models/entrada.py
from pydantic import BaseModel, Field


class EquipamentoEntrada(BaseModel):
    tag: str                = Field(..., examples=["MTR-004"])
    modelo: str
    fabricante: str
    potencia_cv: float        = 0
    tensao_v: int              = 380
    corrente_nominal_a: float = 0
    rotacao_rpm: int           = 0
    fator_potencia: float     = 0.86
    classe_isolamento: str    = "F"
    ip: str                    = "IP55"
    peso_kg: float             = 0
    local: str                 = ""
    status: str                 = "Operacional"
```

```python
# backend/models/saida.py
from pydantic import BaseModel


class EquipamentoSaida(BaseModel):
    tag: str
    modelo: str
    fabricante: str
    potencia_cv: float
    tensao_v: int
    corrente_nominal_a: float
    rotacao_rpm: int
    fator_potencia: float
    classe_isolamento: str
    ip: str
    peso_kg: float
    local: str
    status: str
    cadastrado_em: str


class LocalizacaoSaida(BaseModel):
    planta: str
    area: str


class LeituraSaida(BaseModel):
    tag: str
    timestamp: str
    tensao_v: float
    corrente_a: float
    temp_c: float
    vibracao_mms: float
    rotacao_rpm: float
    falha: int
    severidade_temp: str       # "normal" | "aviso" | "critico"
    severidade_vibracao: str   # "normal" | "aviso" | "critico"


class MensagemSaida(BaseModel):
    mensagem: str
```

## 1.3 `auth/seguranca.py` — protegendo as rotas com API Key

```python
# backend/auth/seguranca.py
import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

API_KEY = os.getenv("API_KEY", "chave-local-dev")


def verificar_chave(chave: str = Security(api_key_header)) -> str:
    """
    Dependência de segurança usada em todos os routers.
    Toda requisição precisa mandar o header X-API-Key com o valor correto.
    """
    if chave != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida.",
        )
    return chave
```

## 1.4 `routers/` — os endpoints

```python
# backend/routers/equipamentos.py
from fastapi import APIRouter, HTTPException, Security

from auth.seguranca import verificar_chave
from models.entrada import EquipamentoEntrada
from models.saida import EquipamentoSaida, MensagemSaida
import providers.equipamento_provider as eq_provider

router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])


@router.get("", response_model=list[EquipamentoSaida])
def listar_equipamentos(_: str = Security(verificar_chave)):
    """Lista todos os motores cadastrados."""
    return eq_provider.listar_todos()


@router.get("/tags", response_model=list[str])
def listar_tags(_: str = Security(verificar_chave)):
    """Lista só as TAGs — usado para popular dropdowns no front."""
    return eq_provider.tags_disponiveis()


@router.get("/{tag}", response_model=EquipamentoSaida)
def buscar_equipamento(tag: str, _: str = Security(verificar_chave)):
    eq = eq_provider.buscar_por_tag(tag)
    if not eq:
        raise HTTPException(status_code=404, detail=f"Equipamento {tag} não encontrado.")
    return eq


@router.post("", response_model=MensagemSaida, status_code=201)
def salvar_equipamento(entrada: EquipamentoEntrada, _: str = Security(verificar_chave)):
    """Cria ou atualiza um equipamento (upsert pela TAG)."""
    sucesso, mensagem = eq_provider.salvar(entrada.model_dump())
    if not sucesso:
        raise HTTPException(status_code=400, detail=mensagem)
    return {"mensagem": mensagem}
```

```python
# backend/routers/plantas.py
from fastapi import APIRouter, Security

from auth.seguranca import verificar_chave
from models.saida import LocalizacaoSaida
import providers.planta_provider as planta_provider

router = APIRouter(prefix="/plantas", tags=["Plantas"])


@router.get("", response_model=list[str])
def listar_plantas(_: str = Security(verificar_chave)):
    return planta_provider.listar_plantas()


@router.get("/{planta}/areas", response_model=list[str])
def listar_areas(planta: str, _: str = Security(verificar_chave)):
    return planta_provider.listar_areas(planta)


@router.get("/{planta}/areas/{area}/equipamentos", response_model=list[str])
def listar_equipamentos_area(planta: str, area: str, _: str = Security(verificar_chave)):
    return planta_provider.listar_equipamentos(planta, area)


@router.get("/localizacao/{tag}", response_model=LocalizacaoSaida)
def buscar_localizacao(tag: str, _: str = Security(verificar_chave)):
    planta, area = planta_provider.buscar_localizacao(tag)
    return {"planta": planta, "area": area}
```

```python
# backend/routers/sensores.py
from fastapi import APIRouter, Security

from auth.seguranca import verificar_chave
from models.saida import LeituraSaida
import providers.sensor_provider as sensor_provider

router = APIRouter(prefix="/sensores", tags=["Sensores"])

# Limites ISO 10816 (Classe II) — regra de negócio, por isso vive no back-end.
# Antes essa lógica estava duplicada em sensor_pipeline.py E dashboard_pipeline.py
# no front-end. Agora existe em UM único lugar.
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


def _com_severidade(leitura: dict) -> dict:
    return {
        **leitura,
        "severidade_temp":     _severidade("temp_c", leitura["temp_c"]),
        "severidade_vibracao": _severidade("vibracao_mms", leitura["vibracao_mms"]),
    }


@router.get("/{tag}/leitura-atual", response_model=LeituraSaida)
def leitura_atual(tag: str, _: str = Security(verificar_chave)):
    leitura = sensor_provider.leitura_atual(tag)
    return _com_severidade(leitura)


@router.get("/{tag}/historico", response_model=list[LeituraSaida])
def historico(tag: str, n: int = 48, _: str = Security(verificar_chave)):
    pontos = sensor_provider.historico_simulado(tag, n_pontos=n)
    return [_com_severidade(p) for p in pontos]
```

## 1.5 `main.py` — juntando tudo

```python
# backend/main.py
from dotenv import load_dotenv
load_dotenv()  # precisa vir ANTES de importar auth/routers, que leem os.getenv no import

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import equipamentos, plantas, sensores

app = FastAPI(title="Forzy Digital Twin API", version="1.0.0")

# CORS — o Gradio local roda em http://localhost:7860 por padrão
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7860"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(equipamentos.router, prefix="/v1")
app.include_router(plantas.router,      prefix="/v1")
app.include_router(sensores.router,     prefix="/v1")


@app.get("/")
def raiz():
    return {"status": "ok", "servico": "Forzy Digital Twin API"}
```

## 1.6 Variáveis de ambiente do back-end

```bash
# backend/.env  (nunca commitar — colocar no .gitignore)
API_KEY=chave-super-secreta-dev
```

```bash
# backend/requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

```bash
pip install -r backend/requirements.txt
```

## 1.7 Rodando e testando o back-end (antes de tocar no front)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Valide isoladamente, **sem o Gradio rodando ainda**:

1. Acesse `http://localhost:8000/docs` — o Swagger mostra os três grupos de endpoints (Equipamentos, Plantas, Sensores).
2. No Swagger, clique em **Authorize** e cole a mesma chave do `.env` (`chave-super-secreta-dev`).
3. Teste `GET /v1/equipamentos` — deve retornar a lista de motores do `motor.db`.
4. Teste sem autorizar — deve retornar `401 Unauthorized`.
5. Teste `GET /v1/sensores/MTR-001/leitura-atual` — confira que `severidade_temp` e `severidade_vibracao` aparecem calculados.

Ou via terminal com `curl`:

```bash
curl -H "X-API-Key: chave-super-secreta-dev" http://localhost:8000/v1/equipamentos/tags
```

**Só avance para a Parte 2 depois que o back-end estiver respondendo corretamente sozinho.** Depurar os dois lados juntos, sem saber se o problema é no back ou no front, é a forma mais lenta de trabalhar.

---

# PARTE 2 — FRONT-END (Gradio)

Agora a pasta `sprint_antiga/` vira `frontend/`. A estrutura de `app.py`, `ui/`, `state/` e `features/` **não muda em nenhuma linha** — é a prova de que a separação está bem feita: a UI nunca soube como os dados chegavam, então trocar "de onde vêm" não deveria afetá-la.

```
frontend/
├── app.py                          ← SEM alteração
├── ui/sidebar.py                   ← SEM alteração
├── state/app_state.py              ← SEM alteração
├── features/
│   ├── equipamentos/page.py        ← SEM alteração
│   ├── cadastro/page.py            ← SEM alteração
│   ├── sensores/page.py            ← SEM alteração
│   └── dashboard/page.py           ← SEM alteração
├── pipelines/
│   ├── cadastro_pipeline.py        ← muda só o import
│   ├── sensor_pipeline.py          ← muda o import + remove classificação local
│   └── dashboard_pipeline.py       ← muda o import + remove classificação local
├── providers/
│   └── api_provider.py             ← NOVO — substitui os três providers antigos
├── .env
└── requirements.txt
```

## 2.1 `providers/api_provider.py` — a nova camada de acesso a dados

Esta é a peça central da refatoração no front-end. Ela expõe **as mesmas funções** que `equipamento_provider.py`, `sensor_provider.py` e `planta_provider.py` expunham — só que por trás, em vez de abrir o SQLite, faz uma chamada HTTP autenticada para o back-end.

```python
# frontend/providers/api_provider.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "chave-local-dev")

_HEADERS = {"X-API-Key": API_KEY}
_TIMEOUT = 10


def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_HEADERS, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        print(f"[api_provider] Não foi possível conectar ao back-end em {API_URL}.")
        return None
    except requests.Timeout:
        print(f"[api_provider] Tempo esgotado ao chamar {path}.")
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        print(f"[api_provider] Erro {e.response.status_code} em {path}: {e.response.text}")
        return None


def _post(path: str, corpo: dict) -> tuple[bool, str]:
    try:
        r = requests.post(f"{API_URL}{path}", json=corpo, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        return True, r.json().get("mensagem", "Operação realizada com sucesso.")
    except requests.ConnectionError:
        return False, f"Não foi possível conectar ao back-end em {API_URL}."
    except requests.Timeout:
        return False, "A requisição demorou mais que o esperado. Tente novamente."
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except ValueError:
            detail = str(e)
        return False, detail


# ---------------------------------------------------------------------------
# Equipamentos — mesma interface pública de equipamento_provider.py
# ---------------------------------------------------------------------------

def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos") or []


def tags_disponiveis() -> list[str]:
    return _get("/v1/equipamentos/tags") or []


def buscar_por_tag(tag: str) -> dict | None:
    return _get(f"/v1/equipamentos/{tag}")


def salvar(dados: dict) -> tuple[bool, str]:
    return _post("/v1/equipamentos", dados)


# ---------------------------------------------------------------------------
# Plantas — mesma interface pública de planta_provider.py
# ---------------------------------------------------------------------------

def listar_plantas() -> list[str]:
    return _get("/v1/plantas") or []


def listar_areas(planta: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas") or []


def listar_equipamentos(planta: str, area: str) -> list[str]:
    return _get(f"/v1/plantas/{planta}/areas/{area}/equipamentos") or []


def buscar_localizacao(tag: str) -> tuple[str, str]:
    loc = _get(f"/v1/plantas/localizacao/{tag}")
    if not loc:
        return "", ""
    return loc["planta"], loc["area"]


# ---------------------------------------------------------------------------
# Sensores — mesma interface pública de sensor_provider.py
# (a severidade agora vem pronta do back-end, dentro do dicionário)
# ---------------------------------------------------------------------------

def leitura_atual(tag: str) -> dict:
    return _get(f"/v1/sensores/{tag}/leitura-atual") or {
        "tag": tag, "timestamp": "", "tensao_v": 0, "corrente_a": 0,
        "temp_c": 0, "vibracao_mms": 0, "rotacao_rpm": 0, "falha": 0,
        "severidade_temp": "normal", "severidade_vibracao": "normal",
    }


def historico_simulado(tag: str, n_pontos: int = 48) -> list[dict]:
    return _get(f"/v1/sensores/{tag}/historico", params={"n": n_pontos}) or []
```

> Repare que essa função `_get`/`_post` centraliza o tratamento de erro de rede — nenhuma feature/pipeline precisa saber lidar com `ConnectionError` ou `401`. Isso é exatamente o mesmo papel que o `api_provider.py` tinha no exemplo genérico da versão anterior deste workshop.

## 2.2 Atualizando as `pipelines/` — o que muda de fato

### `pipelines/cadastro_pipeline.py` — só o import muda

```python
# frontend/pipelines/cadastro_pipeline.py
# ANTES: import providers.equipamento_provider as eq_provider
import providers.api_provider as eq_provider

# NADA MAIS muda neste arquivo — listar_para_tabela(), salvar_equipamento(),
# carregar_equipamento() e ficha_tecnica_markdown() continuam idênticas,
# porque eq_provider.listar_todos(), eq_provider.salvar() e
# eq_provider.buscar_por_tag() existem com a mesma assinatura no api_provider.
```

Todo o resto do arquivo (as funções `listar_para_tabela`, `salvar_equipamento`, `carregar_equipamento`, `ficha_tecnica_markdown`) permanece **exatamente igual** ao `sprint_antiga/pipelines/cadastro_pipeline.py`.

### `pipelines/sensor_pipeline.py` — import + remoção da classificação local

A classificação de severidade (função `_classificar_severidade` e o dicionário `_LIMITES`) **sai daqui** — ela agora vive em `backend/routers/sensores.py`. O pipeline só formata o que já vem pronto da API.

```python
# frontend/pipelines/sensor_pipeline.py
import providers.api_provider as api_provider

COLUNAS_HISTORICO = ["Timestamp", "Tensão (V)", "Corrente (A)", "Temp (°C)", "Vibração (mm/s)", "RPM"]

_ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def leitura_como_markdown(tag: str) -> str:
    """
    Retorna a leitura atual do equipamento formatada como Markdown.

    A severidade de cada grandeza já vem calculada pelo back-end
    (campos severidade_temp / severidade_vibracao) — este pipeline
    só decide como exibir, não decide o que é normal/aviso/crítico.
    """
    leitura = api_provider.leitura_atual(tag)
    if not leitura or not leitura.get("timestamp"):
        return f"_Não foi possível obter a leitura de **{tag}**._"

    md  = f"## 📡 Leitura — {tag}\n"
    md += f"**Timestamp:** `{leitura['timestamp']}`\n\n"
    md += "| Grandeza | Valor | Unidade | Status |\n"
    md += "|---|---|---|---|\n"
    md += f"| Tensão (V) | **{leitura['tensao_v']}** | V | 🟢 |\n"
    md += f"| Corrente (A) | **{leitura['corrente_a']}** | A | 🟢 |\n"
    md += f"| Temperatura (°C) | **{leitura['temp_c']}** | °C | {_ICONE_SEV[leitura['severidade_temp']]} |\n"
    md += f"| Vibração (mm/s) | **{leitura['vibracao_mms']}** | mm/s | {_ICONE_SEV[leitura['severidade_vibracao']]} |\n"
    md += f"| Rotação (RPM) | **{leitura['rotacao_rpm']}** | RPM | 🟢 |\n"
    return md


def historico_para_tabela(tag: str) -> list[list]:
    """
    Retorna o histórico de leituras como lista de listas, pronto para
    o gr.Dataframe. Os dados já chegam prontos do back-end — aqui só
    reorganizamos em linhas na ordem de COLUNAS_HISTORICO.
    """
    historico = api_provider.historico_simulado(tag)
    return [
        [h["timestamp"], h["tensao_v"], h["corrente_a"], h["temp_c"], h["vibracao_mms"], h["rotacao_rpm"]]
        for h in historico
    ]
```

### `pipelines/dashboard_pipeline.py` — import + reuso da severidade da API

```python
# frontend/pipelines/dashboard_pipeline.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import providers.api_provider as api_provider

_ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def _icone_status(status: str) -> str:
    return {"Operacional": "🟢", "Em Manutenção": "🟡", "Desligado": "⚫"}.get(status, "⚪")


def cards_telemetria_md(tag: str) -> str:
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return f"_Equipamento **{tag}** não encontrado no cadastro._"

    leitura = api_provider.leitura_atual(tag)

    cor_temp = _ICONE_SEV[leitura["severidade_temp"]]
    cor_vibr = _ICONE_SEV[leitura["severidade_vibracao"]]

    md  = f"### {_icone_status(eq['status'])} **{tag}** — {eq['modelo']} | Status: _{eq['status']}_\n"
    md += f"`Leitura em: {leitura['timestamp']}`\n\n"
    md += "| Grandeza | Valor | Unidade | Alerta |\n"
    md += "|---|---|---|:---:|\n"
    md += f"| Temperatura de Carcaça | **{leitura['temp_c']}** | °C | {cor_temp} |\n"
    md += f"| Vibração RMS (ISO 10816) | **{leitura['vibracao_mms']}** | mm/s | {cor_vibr} |\n"
    md += f"| Corrente de Fase | **{leitura['corrente_a']}** | A | 🟢 |\n"
    md += f"| Tensão Linha-Linha | **{leitura['tensao_v']}** | V | 🟢 |\n"
    md += f"| Rotação Real | **{leitura['rotacao_rpm']}** | RPM | 🟢 |\n"
    md += "\n_🟢 Normal · 🟡 Aviso · 🔴 Crítico — classificação calculada pelo back-end_"
    return md


def grafico_historico(tag: str):
    """
    Monta o gráfico Plotly com 4 subplots (Temperatura, Vibração, Corrente, Rotação).

    Nota de aula: os valores 75/90 e 4.5/7.1 usados aqui para desenhar as
    linhas de referência são os MESMOS limites que o back-end usa para
    calcular severidade_temp/severidade_vibracao (backend/routers/sensores.py).
    Hoje eles estão duplicados como constantes de desenho porque o gráfico
    só precisa da posição das linhas, não da classificação em si.
    Exercício proposto: criar GET /v1/sensores/limites no back-end e buscar
    esses valores em vez de hardcodar — eliminando a duplicação.
    """
    historico = api_provider.historico_simulado(tag)

    timestamps = [h["timestamp"]    for h in historico]
    temp       = [h["temp_c"]       for h in historico]
    vibracao   = [h["vibracao_mms"] for h in historico]
    corrente   = [h["corrente_a"]   for h in historico]
    rpm        = [h["rotacao_rpm"]  for h in historico]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🌡️ Temperatura (°C)",
            "📳 Vibração (mm/s)",
            "⚡ Corrente (A)",
            "🔄 Rotação (RPM)",
        ),
        shared_xaxes=False,
        vertical_spacing=0.18,
        horizontal_spacing=0.10,
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=temp, name="Temp °C",
                   line=dict(color="#e74c3c", width=2), fill="tozeroy",
                   fillcolor="rgba(231,76,60,0.08)"),
        row=1, col=1,
    )
    fig.add_hline(y=75, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 75°C", annotation_position="top right", row=1, col=1)
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="Crítico 90°C", annotation_position="top right", row=1, col=1)

    fig.add_trace(
        go.Scatter(x=timestamps, y=vibracao, name="Vibração mm/s",
                   line=dict(color="#9b59b6", width=2), fill="tozeroy",
                   fillcolor="rgba(155,89,182,0.08)"),
        row=1, col=2,
    )
    fig.add_hline(y=4.5, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 4.5", annotation_position="top right", row=1, col=2)
    fig.add_hline(y=7.1, line_dash="dash", line_color="red",
                  annotation_text="Crítico 7.1", annotation_position="top right", row=1, col=2)

    fig.add_trace(
        go.Scatter(x=timestamps, y=corrente, name="Corrente A",
                   line=dict(color="#3498db", width=2), fill="tozeroy",
                   fillcolor="rgba(52,152,219,0.08)"),
        row=2, col=1,
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=rpm, name="RPM",
                   line=dict(color="#27ae60", width=2), fill="tozeroy",
                   fillcolor="rgba(39,174,96,0.08)"),
        row=2, col=2,
    )

    fig.update_layout(
        title=dict(text=f"📈 Histórico 24h — {tag}", font=dict(size=16)),
        height=480,
        showlegend=False,
        margin=dict(t=80, b=40, l=50, r=40),
        paper_bgcolor="white",
        plot_bgcolor="#f9f9f9",
    )
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9))
    return fig


def placa_md(tag: str) -> str:
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return "_Nenhum equipamento selecionado._"

    return f"""
> 📷 **Simulação** — em produção, esta seção exibirá a foto real da placa
> extraída via Visão Computacional (Sprint 3).

```
╔══════════════════════════════════════════════╗
║          PLACA DE IDENTIFICAÇÃO              ║
╠══════════════════════════════════════════════╣
║  TAG:            {eq['tag']}
║  Modelo:         {eq['modelo']}
║  Fabricante:     {eq['fabricante']}
╠══════════════════════════════════════════════╣
║  Potência:       {eq['potencia_cv']} cv
║  Tensão:         {eq['tensao_v']} V
║  Corrente Nom.:  {eq['corrente_nominal_a']} A
║  Fator de Pot.:  {eq['fator_potencia']}
║  Rotação:        {eq['rotacao_rpm']} RPM
╠══════════════════════════════════════════════╣
║  Isolamento:     Classe {eq['classe_isolamento']}
║  Proteção:       {eq['ip']}
║  Peso:           {eq['peso_kg']} kg
╚══════════════════════════════════════════════╝
```
"""
```

`planta_provider` também precisa ser referenciado — nas features `dashboard/page.py` e `equipamentos/page.py` havia `import providers.planta_provider as planta_provider` e `import providers.equipamento_provider as eq_provider` **diretamente na página**, não só no pipeline. Ajuste também esses imports para `providers.api_provider`:

```python
# frontend/features/dashboard/page.py
# ANTES: import providers.planta_provider as planta_provider
import providers.api_provider as planta_provider   # mesma interface: listar_plantas(), listar_areas(), listar_equipamentos(), buscar_localizacao()
```

```python
# frontend/features/equipamentos/page.py
# ANTES: import providers.equipamento_provider as eq_provider
# (nesta página, eq_provider só era usado dentro de pipeline.* — confira se o
#  import direto ainda é necessário; se não for, pode ser removido)
```

```python
# frontend/features/sensores/page.py
# ANTES: import providers.equipamento_provider as eq_provider
import providers.api_provider as eq_provider   # usado para tags_disponiveis() no dropdown
```

## 2.3 Variáveis de ambiente do front-end

```bash
# frontend/.env  (nunca commitar)
API_URL=http://localhost:8000
API_KEY=chave-super-secreta-dev
```

```bash
# frontend/requirements.txt
gradio>=4.44.0
plotly>=5.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

O `.env` de cada lado deve estar no `.gitignore` — assim como fazíamos com `App.config` no ecossistema .NET. **Nunca** commitem `API_KEY`.

---

# 3. Rodando a Arquitetura Completa

Dois terminais, dois processos:

```bash
# Terminal 1 — back-end
cd backend
uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2 — front-end
cd frontend
python app.py
```

Roteiro de verificação:

1. `http://localhost:8000/docs` — endpoints documentados, `/v1/equipamentos` responde `401` sem chave e `200` com chave.
2. No terminal do back-end, acompanhe os logs de request chegando quando você interage com o Gradio.
3. Abra o Gradio (a porta que `app.launch()` informar no terminal) e:
   - Veja a lista de equipamentos carregando (chamou `GET /v1/equipamentos`).
   - Clique em "Ver Ficha Técnica" — deve buscar o equipamento pela TAG.
   - Cadastre um equipamento novo — deve fazer `POST /v1/equipamentos` e refletir na lista.
   - Vá em "Dados de Sensores" — deve chamar `leitura-atual` e `historico`.
   - Vá em "Dashboard", navegue Planta → Área → Equipamento — deve chamar os endpoints de `/v1/plantas`.
4. Derrube o back-end (`Ctrl+C` no Terminal 1) e tente usar o Gradio de novo — a mensagem de erro de conexão deve aparecer no lugar de uma tela quebrada (é o que o tratamento de `ConnectionError` no `api_provider` garante).

---

# 4. O Que Mudou e Por Que Vale a Pena

| Aspecto | Antes (monolito Gradio + SQLite) | Depois (Gradio + FastAPI) |
|---|---|---|
| Acesso a dados | Direto no processo do Gradio | Isolado atrás de uma API HTTP |
| Concorrência | Duas abas = duas conexões SQLite no mesmo processo Gradio | Back-end pode escalar/gerenciar pool de conexões independente do front |
| Reutilização | Lógica de negócio presa ao Gradio | Qualquer cliente (app mobile, outro dashboard, script) pode consumir a mesma API |
| Regra de severidade ISO 10816 | Duplicada em `sensor_pipeline.py` e `dashboard_pipeline.py` | Centralizada em `backend/routers/sensores.py` — uma fonte de verdade |
| Testabilidade | Difícil testar upsert/validação isolado da UI | `providers/` e `routers/` testáveis via `curl`/Pytest, sem subir o Gradio |
| Segurança | Qualquer processo local lê/grava `motor.db` sem controle | Toda escrita passa por validação + `X-API-Key` |
| Deploy | Um processo só | Front e back fazem deploy separado, em servidores diferentes se necessário |

---

# Referências

- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [FastAPI — Security Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI — Bigger Applications (APIRouter)](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [12-Factor App — Config](https://12factor.net/config)
- [ISO 10816 — Mechanical vibration evaluation](https://www.iso.org/standard/23076.html)
