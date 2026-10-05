# =============================================================================
# pipelines/cadastro_pipeline.py — Dados de cadastro prontos para a tela
#
# Mudança de contrato em relação à versão desktop: as funções deixam de
# devolver uma TABELA (DataFrame, Markdown) e passam a devolver ESTRUTURAS
# (listas de dicionários, pares rótulo/valor). Quem decide se isso vira uma
# tabela, um card ou uma lista é o componente da camada ui/ — e no celular a
# resposta quase nunca é "tabela".
# =============================================================================

import providers.api_provider as eq_provider
from pipelines.formatacao import numero


def listar_equipamentos(busca: str = "", status: str | None = None) -> list[dict]:
    """
    Equipamentos filtrados por texto (TAG, modelo, fabricante ou local) e por
    status operacional, já com os textos que o card exibe.
    """
    termo = busca.strip().lower()
    itens = []
    for e in eq_provider.listar_todos():
        alvo = f"{e['tag']} {e['modelo']} {e['fabricante']} {e['local']}".lower()
        if termo and termo not in alvo:
            continue
        if status and e["status"] != status:
            continue
        itens.append({
            "tag": e["tag"],
            "titulo": f"{e['modelo']} · {e['fabricante']}",
            "detalhe": f"{numero(e['potencia_cv'], 1)} cv · {e['tensao_v']} V",
            "local": e["local"] or "Local não informado",
            "status": e["status"],
        })
    return itens


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
    """Monta o corpo do POST /v1/equipamentos e devolve (sucesso, mensagem)."""
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
    """Equipamento cru, para pré-preencher o formulário de edição."""
    if not tag:
        return None
    return eq_provider.buscar_por_tag(tag.strip().upper())


def ficha_tecnica(tag: str) -> dict | None:
    """
    Ficha técnica em seções de pares rótulo/valor.

    Antes era uma string Markdown com tabelas — que, numa tela de 360 px,
    quebrava números no meio ("176 / 0.0"). Pares rótulo/valor se adaptam a
    qualquer largura.
    """
    eq = eq_provider.buscar_por_tag(tag)
    if not eq:
        return None
    return {
        "tag": eq["tag"],
        "titulo": eq["modelo"],
        "status": eq["status"],
        "secoes": [
            ("Identificação", [
                ("Fabricante", eq["fabricante"]),
                ("Local", eq["local"] or "—"),
                ("Cadastrado em", eq["cadastrado_em"]),
            ]),
            ("Elétrica", [
                ("Potência", f"{numero(eq['potencia_cv'], 1)} cv"),
                ("Tensão", f"{eq['tensao_v']} V"),
                ("Corrente nominal", f"{numero(eq['corrente_nominal_a'], 1)} A"),
                ("Fator de potência", numero(eq["fator_potencia"], 2)),
            ]),
            ("Mecânica e construção", [
                ("Rotação", f"{numero(eq['rotacao_rpm'], 0)} RPM"),
                ("Classe de isolamento", eq["classe_isolamento"]),
                ("Grau de proteção", eq["ip"]),
                ("Peso", f"{numero(eq['peso_kg'], 1)} kg"),
            ]),
        ],
    }
