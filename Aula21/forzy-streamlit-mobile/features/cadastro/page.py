# =============================================================================
# features/cadastro/page.py — Ficha técnica e formulário de cadastro
#
# Mudanças para o celular:
#   - a ficha deixa de ser tabela Markdown e vira pares rótulo/valor;
#   - o formulário vira uma coluna, em seções nomeadas; campos que formam
#     par (tensão e corrente, por exemplo) usam st.columns, que o Streamlit
#     empilha sozinho em telas estreitas e mantém lado a lado no desktop;
#   - a TAG é validada no próprio campo, antes de gastar uma requisição.
# =============================================================================

import streamlit as st

import pipelines.cadastro_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state
from ui import componentes as ui

FABRICANTES = ["WEG", "Siemens", "ABB", "Nidec", "Voges", "Outro"]
CLASSES_ISOLAMENTO = ["A", "B", "F", "H"]
IPS = ["IP21", "IP44", "IP54", "IP55", "IP65", "IP66"]
TENSOES = [220, 380, 440, 480, 690]
STATUS = ["Operacional", "Em Manutenção", "Desligado"]

VISOES = {"ficha": ":material/description: Ficha", "edicao": ":material/edit: Editar"}

_VAZIO = {
    "tag": "", "modelo": "", "fabricante": "WEG", "potencia_cv": 1.0,
    "tensao_v": 380, "corrente_nominal_a": 1.0, "fator_potencia": 0.86,
    "rotacao_rpm": 1760, "classe_isolamento": "F", "ip": "IP55",
    "peso_kg": 1.0, "local": "", "status": "Operacional",
}


def _indice(opcoes: list, valor, padrao: int = 0) -> int:
    try:
        return opcoes.index(valor)
    except ValueError:
        return padrao


def _ficha(tag: str) -> None:
    """Ficha técnica em seções de pares rótulo/valor."""
    ficha = pipeline.ficha_tecnica(tag)
    if not ficha:
        ui.estado_vazio("Este motor ainda não tem ficha. Use **Editar** para cadastrá-lo.")
        return
    with st.container(border=True):
        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(f"### {ficha['tag']}")
            ui.selo_status(ficha["status"])
        st.caption(ficha["titulo"])
    for titulo, pares in ficha["secoes"]:
        st.markdown(f"**{titulo}**")
        ui.pares_rotulo_valor(pares)
        ui.espaco("xs")


def _formulario(base: dict) -> None:
    """Formulário em coluna única, por seções; pares viram colunas só onde cabem."""
    with st.form("form_equipamento", border=False):
        st.markdown("**Identificação**")
        f_tag = st.text_input("TAG", value=base["tag"], placeholder="MTR-021",
                              validate=(r"^MTR-\d{3}$", "Use o formato MTR-000, por exemplo MTR-021."))
        f_modelo = st.text_input("Modelo", value=base["modelo"], placeholder="W22 160L")
        f_fabricante = st.selectbox("Fabricante", FABRICANTES, index=_indice(FABRICANTES, base["fabricante"]))

        st.markdown("**Elétrica**")
        c1, c2 = st.columns(2)
        f_potencia = c1.number_input("Potência (cv)", min_value=0.5, value=float(base["potencia_cv"] or 1), step=0.5)
        f_tensao = c2.selectbox("Tensão (V)", TENSOES, index=_indice(TENSOES, base["tensao_v"], 1))
        c1, c2 = st.columns(2)
        f_corrente = c1.number_input("Corrente (A)", min_value=0.1, value=float(base["corrente_nominal_a"] or 1), step=0.1)
        f_fp = c2.number_input("Fator de potência", min_value=0.60, max_value=1.00,
                               value=float(base["fator_potencia"] or 0.86), step=0.01)

        st.markdown("**Mecânica e construção**")
        c1, c2 = st.columns(2)
        f_rotacao = c1.number_input("Rotação (RPM)", min_value=500, value=int(base["rotacao_rpm"] or 1760), step=10)
        f_peso = c2.number_input("Peso (kg)", min_value=1.0, value=float(base["peso_kg"] or 1), step=1.0)
        c1, c2 = st.columns(2)
        f_classe = c1.selectbox("Isolamento", CLASSES_ISOLAMENTO, index=_indice(CLASSES_ISOLAMENTO, base["classe_isolamento"], 2))
        f_ip = c2.selectbox("Proteção (IP)", IPS, index=_indice(IPS, base["ip"], 3))

        st.markdown("**Localização e estado**")
        f_local = st.text_input("Local", value=base["local"], placeholder="Planta A — Linha 1")
        f_status = st.selectbox("Status operacional", STATUS, index=_indice(STATUS, base["status"]))

        with st.container(key="acoes_cadastro"):
            enviado = st.form_submit_button("Salvar", type="primary", icon=":material/save:", width="stretch")

    if not enviado:
        return
    if not f_tag.strip() or not f_modelo.strip():
        st.error("TAG e Modelo são obrigatórios.")
        return

    sucesso, mensagem = pipeline.salvar_equipamento(
        f_tag, f_modelo, f_fabricante, f_potencia, f_tensao, f_corrente,
        f_rotacao, f_fp, f_classe, f_ip, f_peso, f_local, f_status,
    )
    if not sucesso:
        ui.estado_erro(mensagem)
        return
    api_provider.limpar_cache()
    st.session_state["_aviso_global"] = mensagem
    app_state.ir_para("cadastro", tag=f_tag.strip().upper(), modo="edicao")


def render() -> None:
    tag = app_state.tag_selecionada()
    modo = app_state.modo_cadastro()

    if st.button("Motores", icon=":material/arrow_back:", type="tertiary"):
        app_state.ir_para("equipamentos")

    ui.titulo_tela("Novo motor" if modo == "novo" else f"Motor {tag}")

    if modo == "novo" or not tag:
        _formulario(dict(_VAZIO))
        return

    visao = st.segmented_control("Visão", list(VISOES), format_func=VISOES.get, default="ficha",
                                 required=True, key=f"visao_{tag}", label_visibility="collapsed", width="stretch")
    if visao == "ficha":
        _ficha(tag)
    else:
        eq = pipeline.carregar_equipamento(tag) or {}
        _formulario({**_VAZIO, **eq})
