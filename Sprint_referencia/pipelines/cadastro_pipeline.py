# =============================================================================
# pipelines/cadastro_pipeline.py — Lógica de negócio do cadastro
#
# O que é um pipeline?
# --------------------
# É a camada intermediária entre a UI (features) e os dados (providers).
# O pipeline conhece as regras de negócio: como formatar dados para a UI,
# quais campos são obrigatórios, como transformar um dicionário do provider
# em algo que o Gradio consiga exibir.
#
# O que o pipeline NÃO faz:
#   - Não cria componentes Gradio (isso é responsabilidade das features)
#   - Não acessa banco de dados diretamente (isso é responsabilidade dos providers)
#
# Fluxo de dados:
#   Feature (UI) → chama pipeline → pipeline chama provider → retorna para feature
# =============================================================================

import providers.equipamento_provider as eq_provider


# ---------------------------------------------------------------------------
# Constante exportada: define as colunas do gr.Dataframe na Home.
# Fica aqui (e não na feature) porque é o pipeline que sabe quais campos
# do equipamento fazem sentido exibir na tabela resumida.
# ---------------------------------------------------------------------------
COLUNAS_TABELA = ["TAG", "Modelo", "Fabricante", "Potência (cv)", "Tensão (V)", "Local", "Status", "Cadastro"]


def listar_para_tabela() -> list[list]:
    """
    Busca todos os equipamentos e os formata como lista de listas.

    O gr.Dataframe do Gradio espera uma lista de listas, onde cada lista
    interna é uma linha da tabela — por isso a transformação aqui.
    """
    equipamentos = eq_provider.listar_todos()

    # Cada equipamento vira uma linha com os campos na ordem de COLUNAS_TABELA
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
    Recebe os valores do formulário, monta o dicionário e delega ao provider.

    Os parâmetros chegam diretamente dos componentes do formulário Gradio,
    por isso temos um parâmetro para cada campo — sem dicionário intermediário.

    Retorna uma string de feedback com ícone (✅ ou ❌) para exibir na UI.
    """
    # Monta o dicionário para o provider; aplica fallbacks para campos numéricos
    # que podem chegar como None quando o usuário não preencheu o campo
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

    # Prefixo visual para o usuário identificar rapidamente o resultado
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

    Usamos Markdown porque o gr.Markdown do Gradio renderiza tabelas,
    negrito e outros elementos nativamente — sem precisar de HTML.

    Retorna string Markdown pronta para passar a um gr.Markdown.
    """
    eq = eq_provider.buscar_por_tag(tag)

    # Se o equipamento não existe, retorna mensagem informativa
    if not eq:
        return f"_Equipamento **{tag}** não encontrado._"

    # Ícone visual para o status — facilita a leitura rápida
    icone_status = {
        "Operacional":   "🟢",
        "Em Manutenção": "🟡",
        "Desligado":     "⚫",
    }.get(eq["status"], "⚪")

    # Monta o Markdown com duas tabelas separadas por área técnica
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
