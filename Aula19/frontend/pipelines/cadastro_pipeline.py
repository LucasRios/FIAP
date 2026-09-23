# =============================================================================
# pipelines/cadastro_pipeline.py — Lógica de apresentação do cadastro
#
# Único ponto alterado em relação ao Sprint anterior: o import.
# eq_provider.listar_todos(), .salvar() e .buscar_por_tag() existem com a
# mesma assinatura em providers.api_provider — por isso o resto do arquivo
# não muda uma linha.
# =============================================================================

import providers.api_provider as eq_provider


# ---------------------------------------------------------------------------
# Constante exportada: define as colunas do gr.Dataframe na Home.
# ---------------------------------------------------------------------------
COLUNAS_TABELA = ["TAG", "Modelo", "Fabricante", "Potência (cv)", "Tensão (V)", "Local", "Status", "Cadastro"]


def listar_para_tabela() -> list[list]:
    """
    Busca todos os equipamentos e os formata como lista de listas.

    O gr.Dataframe do Gradio espera uma lista de listas, onde cada lista
    interna é uma linha da tabela — por isso a transformação aqui.
    """
    equipamentos = eq_provider.listar_todos()

    return [
        [
            e["tag"],
            e["modelo"],
            e["fabricante"],
            e["potencia_cv"],
            e["tensao_v"],
            e["local"],
            e["status"],
            e["cadastrado_em"],
        ]
        for e in equipamentos
    ]


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
) -> str:
    """
    Recebe os valores do formulário, monta o dicionário e delega ao
    api_provider (que faz o POST /v1/equipamentos no back-end).

    Retorna uma string de feedback com ícone (✅ ou ❌) para exibir na UI.
    """
    dados = {
        "tag":                tag,
        "modelo":             modelo,
        "fabricante":         fabricante,
        "potencia_cv":        potencia_cv or 0,
        "tensao_v":           tensao_v or 380,
        "corrente_nominal_a": corrente_nominal_a or 0,
        "rotacao_rpm":        rotacao_rpm or 0,
        "fator_potencia":     fator_potencia or 0.86,
        "classe_isolamento":  classe_isolamento,
        "ip":                 ip,
        "peso_kg":            peso_kg or 0,
        "local":              local,
        "status":             status,
    }

    sucesso, mensagem = eq_provider.salvar(dados)

    prefixo = "✅" if sucesso else "❌"
    return f"{prefixo} {mensagem}"


def carregar_equipamento(tag: str) -> dict | None:
    """
    Busca os dados de um equipamento pelo TAG para pré-preencher o formulário.
    Retorna None se não encontrado — a feature trata esse caso.
    """
    return eq_provider.buscar_por_tag(tag)


def ficha_tecnica_markdown(tag: str) -> str:
    """
    Gera a ficha técnica completa de um equipamento formatada em Markdown.
    """
    eq = eq_provider.buscar_por_tag(tag)

    if not eq:
        return f"_Equipamento **{tag}** não encontrado._"

    icone_status = {
        "Operacional":   "🟢",
        "Em Manutenção": "🟡",
        "Desligado":     "⚫",
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
