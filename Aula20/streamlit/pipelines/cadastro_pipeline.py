# =============================================================================
# pipelines/cadastro_pipeline.py — Apresentação dos dados de cadastro
#
# Comparado à versão Gradio, só a função listar_para_tabela mudou: ela
# devolve um DataFrame do pandas em vez de uma lista de listas, porque é
# esse o formato que o st.dataframe espera. Todo o resto é idêntico — a
# prova de que a lógica de apresentação não depende da biblioteca de UI.
# =============================================================================

import pandas as pd

import providers.api_provider as eq_provider

COLUNAS_TABELA = [
    "TAG", "Modelo", "Fabricante", "Potência (cv)",
    "Tensão (V)", "Local", "Status", "Cadastro",
]


def listar_para_tabela() -> pd.DataFrame:
    """Busca todos os equipamentos e devolve um DataFrame pronto para exibição."""
    equipamentos = eq_provider.listar_todos()

    linhas = [
        [e["tag"], e["modelo"], e["fabricante"], e["potencia_cv"],
         e["tensao_v"], e["local"], e["status"], e["cadastrado_em"]]
        for e in equipamentos
    ]
    return pd.DataFrame(linhas, columns=COLUNAS_TABELA)


def salvar_equipamento(
    tag: str,
    modelo: str,
    fabricante: str,
    potencia_cv: float,
    tensao_v: int,
    corrente_nominal_a: float,
    rotacao_rpm: int,
    fator_potencia: float,
    classe_isolamento: str,
    ip: str,
    peso_kg: float,
    local: str,
    status: str,
) -> tuple[bool, str]:
    """
    Monta o corpo da requisição a partir dos campos do formulário e delega
    ao api_provider, que faz o POST /v1/equipamentos.

    Devolve (sucesso, mensagem) — quem escolhe o ícone é a página, usando
    st.success ou st.error.
    """
    dados = {
        "tag": tag.strip().upper(),
        "modelo": modelo.strip(),
        "fabricante": fabricante or "",
        "potencia_cv": potencia_cv or 0,
        "tensao_v": tensao_v or 380,
        "corrente_nominal_a": corrente_nominal_a or 0,
        "rotacao_rpm": rotacao_rpm or 0,
        "fator_potencia": fator_potencia or 0.86,
        "classe_isolamento": classe_isolamento,
        "ip": ip,
        "peso_kg": peso_kg or 0,
        "local": local.strip(),
        "status": status,
    }
    return eq_provider.salvar(dados)


def carregar_equipamento(tag: str) -> dict | None:
    """Busca um equipamento pela TAG para pré-preencher o formulário."""
    if not tag:
        return None
    return eq_provider.buscar_por_tag(tag.strip().upper())


def ficha_tecnica_markdown(tag: str) -> str:
    """Gera a ficha técnica completa do equipamento em Markdown."""
    eq = eq_provider.buscar_por_tag(tag)

    if not eq:
        return f"_Equipamento **{tag}** não encontrado._"

    icone_status = {
        "Operacional": "🟢",
        "Em Manutenção": "🟡",
        "Desligado": "⚫",
    }.get(eq["status"], "⚪")

    return f"""
## {eq['tag']} — {eq['modelo']}
**Status:** {icone_status} {eq['status']} &nbsp;&nbsp; **Fabricante:** {eq['fabricante']}

---
### ⚡ Parâmetros Elétricos
| Grandeza | Valor |
|---|---|
| Potência | {eq['potencia_cv']} cv |
| Tensão | {eq['tensao_v']} V |
| Corrente Nominal | {eq['corrente_nominal_a']} A |
| Fator de Potência | {eq['fator_potencia']} |

### ⚙️ Parâmetros Mecânicos e Construtivos
| Grandeza | Valor |
|---|---|
| Rotação | {eq['rotacao_rpm']} RPM |
| Classe de Isolamento | {eq['classe_isolamento']} |
| Grau de Proteção | {eq['ip']} |
| Peso | {eq['peso_kg']} kg |

### 📍 Localização
**Local:** {eq['local']} &nbsp;&nbsp; **Cadastrado em:** {eq['cadastrado_em']}
"""
