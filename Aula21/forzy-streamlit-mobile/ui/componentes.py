# =============================================================================
# ui/componentes.py — Componentes do design system do Forzy
#
# Cada função aqui é um componente: recebe DADOS (nunca cores ou ícones) e
# decide sozinha como desenhá-los, consultando ui/tokens.py. As páginas em
# features/ montam telas combinando estes componentes — e nunca chamam
# st.badge, st.metric ou st.container(border=True) diretamente para exibir
# um status. É isso que garante que "crítico" tenha a mesma cara em todo lugar.
#
# Hierarquia (Atomic Design):
#   átomos     selo_severidade, selo_status
#   moléculas  pares_rotulo_valor, cartao_grandeza, estado_vazio
#   organismos cartao_equipamento, resumo_motor, grade_grandezas
# =============================================================================

import streamlit as st

from ui.tokens import ESPACO, STATUS_OPERACIONAL, severidade

# ---------------------------------------------------------------------------
# Átomos
# ---------------------------------------------------------------------------

def selo_severidade(chave: str | None) -> None:
    """
    Selo da severidade de uma LEITURA: ícone de forma própria + texto + cor.

    Três canais redundantes de propósito. Quem não distingue verde de
    vermelho, ou quem lê a tela sob o sol, ainda reconhece a forma e lê o texto.
    """
    s = severidade(chave)
    st.badge(s["rotulo"], icon=s["icone"], color=s["cor_nativa"])


def texto_selo(chave: str | None) -> str:
    """
    Selo de severidade como diretiva de Markdown (:red-badge[...]), para usar
    DENTRO de uma frase ou linha de lista, onde st.badge (um bloco) quebraria
    o fluxo. As cores vêm do [theme], logo dos tokens.
    """
    s = severidade(chave)
    return f":{s['cor_nativa']}-badge[{s['simbolo']} {s['rotulo']}]"


def selo_status(status: str) -> None:
    """
    Selo do status OPERACIONAL do cadastro (Operacional, Em Manutenção, Desligado).

    Deliberadamente sem verde, âmbar ou vermelho: essas cores pertencem à
    severidade. Dois conceitos, duas linguagens visuais.
    """
    meta = STATUS_OPERACIONAL.get(status, {"icone": ":material/help:", "cor_nativa": "gray"})
    st.badge(status, icon=meta["icone"], color=meta["cor_nativa"])


# ---------------------------------------------------------------------------
# Moléculas
# ---------------------------------------------------------------------------

def titulo_tela(titulo: str, subtitulo: str | None = None) -> None:
    """Título de tela compacto: no celular, o h1 padrão ocupava um quinto da tela."""
    st.subheader(titulo, anchor=False)
    if subtitulo:
        st.caption(subtitulo)


def pares_rotulo_valor(pares: list[tuple[str, str]]) -> None:
    """
    Lista rótulo/valor em duas pontas da linha.

    Substitui tabelas Markdown e arte ASCII: se adapta a qualquer largura e
    nunca quebra um número no meio.
    """
    for rotulo, valor in pares:
        with st.container(horizontal=True, horizontal_alignment="distribute", gap="small"):
            st.caption(rotulo)
            st.markdown(f"**{valor}**")


def estado_vazio(mensagem: str, icone: str = ":material/info:") -> None:
    """Estado vazio: diz o que fazer, em vez de mostrar uma área em branco."""
    st.info(mensagem, icon=icone)


def estado_erro(mensagem: str) -> None:
    """Estado de erro: o que aconteceu e o que o usuário pode fazer."""
    st.error(mensagem, icon=":material/cloud_off:")


def cartao_grandeza(item: dict, largura: int = 168) -> None:
    """
    Card de uma grandeza: valor grande, tendência em miniatura e severidade.

    A largura fixa faz a grade se reorganizar sozinha: dois cards por linha
    num celular, quatro ou cinco num monitor — sem nenhum breakpoint em Python.
    """
    with st.container(border=True, width=largura, key=f"grandeza_{item['chave']}"):
        if item["severidade"]:
            selo_severidade(item["severidade"])
        else:
            st.caption("Sem limite definido")
        st.metric(
            label=item["nome"],
            value=item["valor"],
            chart_data=item["serie"],
            chart_type="line",
            border=False,
        )


# ---------------------------------------------------------------------------
# Organismos
# ---------------------------------------------------------------------------

def cartao_equipamento(eq: dict) -> str | None:
    """
    Card de um equipamento na lista. Devolve a ação tocada: 'painel', 'ficha' ou None.

    Substitui a linha de tabela com caixa de seleção de 20 px. A área de toque
    agora é o botão inteiro, com a largura do card.
    """
    with st.container(border=True, key=f"equip_{eq['tag']}"):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(f"**{eq['tag']}**")
            selo_status(eq["status"])
        st.markdown(eq["titulo"])
        st.caption(f"{eq['detalhe']}  \n{eq['local']}")

        with st.container(horizontal=True, gap="small", key=f"acoes_{eq['tag']}"):
            if st.button("Painel", icon=":material/monitoring:", type="primary",
                         key=f"painel_{eq['tag']}", width="stretch"):
                return "painel"
            if st.button("Ficha", icon=":material/description:",
                         key=f"ficha_{eq['tag']}", width="stretch"):
                return "ficha"
    return None


def resumo_motor(p: dict) -> None:
    """
    Cabeçalho "status primeiro" do painel: responde "o motor está bem?" antes
    de qualquer número. A chave do container carrega a severidade, o que
    permite ao CSS opcional (ui/estilo.py) pintar a borda lateral.
    """
    with st.container(border=True, key=f"resumo_{p['severidade']}"):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(f"### {p['tag']}")
            selo_severidade(p["severidade"])
        st.markdown(p["explicacao"])
        st.caption(f"{p['titulo']} · {p['local']}  \nLeitura das {p['hora']}")
        selo_status(p["status_operacional"])


def grade_grandezas(itens: list[dict]) -> None:
    """Grade fluida de cards: quebra de linha automática conforme a largura da tela."""
    with st.container(horizontal=True, wrap=True, gap="small"):
        for item in itens:
            cartao_grandeza(item)


def espaco(tamanho: str = "md") -> None:
    """Respiro vertical vindo da escala de espaçamento, nunca de um número solto."""
    st.space(ESPACO[tamanho])
