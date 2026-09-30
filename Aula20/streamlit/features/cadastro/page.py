# =============================================================================
# features/cadastro/page.py — Cadastro técnico do equipamento
#
# Duas visões, escolhidas por um seletor: Ficha Técnica (somente leitura) e
# Edição (formulário). Usamos st.radio em vez de st.tabs porque precisamos
# ABRIR a visão certa por código: quem chega em modo "edicao" deve cair na
# ficha; quem chega em modo "novo", no formulário. O st.tabs não permite
# escolher a aba ativa programaticamente.
#
# O formulário fica dentro de st.form: os campos só são enviados quando o
# botão Salvar é pressionado, em vez de reexecutar o script a cada tecla.
# =============================================================================

import streamlit as st

import pipelines.cadastro_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state

FABRICANTES = ["WEG", "Siemens", "ABB", "Nidec", "Voges", "Outro"]
CLASSES_ISOLAMENTO = ["A", "B", "F", "H"]
IPS = ["IP21", "IP44", "IP54", "IP55", "IP65", "IP66"]
TENSOES = [220, 380, 440, 480, 690]
STATUS = ["Operacional", "Em Manutenção", "Desligado"]

_VAZIO = {
    "tag": "", "modelo": "", "fabricante": "WEG", "potencia_cv": 1.0,
    "tensao_v": 380, "corrente_nominal_a": 1.0, "fator_potencia": 0.86,
    "rotacao_rpm": 1760, "classe_isolamento": "F", "ip": "IP55",
    "peso_kg": 1.0, "local": "", "status": "Operacional",
}


def _indice(opcoes: list, valor, padrao: int = 0) -> int:
    """Índice de um valor na lista de opções, com padrão quando não existe."""
    try:
        return opcoes.index(valor)
    except ValueError:
        return padrao


def render() -> None:
    tag_atual = app_state.tag_selecionada()
    modo = app_state.modo_cadastro()

    st.markdown("## 🔧 Cadastro Técnico do Equipamento")

    if st.button("← Voltar para Equipamentos"):
        app_state.ir_para("equipamentos")

    st.divider()

    # Mensagem guardada pelo salvamento anterior: o st.rerun() apaga a tela,
    # então o aviso precisa atravessar a reexecução dentro do session_state.
    aviso = st.session_state.pop("_cadastro_aviso", None)
    if aviso:
        st.success(aviso)

    # Em modo "edicao" a ficha é a visão inicial; em "novo", o formulário.
    # O valor fica em session_state para o usuário poder alternar depois.
    chave_visao = "cadastro_visao"
    if st.session_state.get("_cadastro_carregado") != (tag_atual, modo):
        st.session_state[chave_visao] = "📄 Ficha Técnica" if (modo == "edicao" and tag_atual) else "✏️ Edição"
        st.session_state["_cadastro_carregado"] = (tag_atual, modo)

    visao = st.radio(
        "Visão",
        ["📄 Ficha Técnica", "✏️ Edição"],
        horizontal=True,
        label_visibility="collapsed",
        key=chave_visao,
    )

    # Valores que alimentam o formulário: do equipamento em edição ou em branco.
    eq = pipeline.carregar_equipamento(tag_atual) if (modo == "edicao" and tag_atual) else None
    base = {**_VAZIO, **(eq or {})}

    if visao == "📄 Ficha Técnica":
        if eq:
            st.markdown(pipeline.ficha_tecnica_markdown(tag_atual))
        else:
            st.info("Preencha os campos na aba **Edição** e salve para criar a ficha técnica.")
        return

    # ── Formulário ──────────────────────────────────────────────────────────
    with st.form("form_equipamento"):
        st.markdown("### Identificação")
        c1, c2, c3 = st.columns(3)
        f_tag = c1.text_input("TAG *", value=base["tag"], placeholder="MTR-004")
        f_modelo = c2.text_input("Modelo *", value=base["modelo"], placeholder="WEG W22 160L")
        f_fabricante = c3.selectbox("Fabricante *", FABRICANTES,
                                    index=_indice(FABRICANTES, base["fabricante"]))

        st.markdown("### ⚡ Parâmetros Elétricos")
        c1, c2, c3, c4 = st.columns(4)
        f_potencia = c1.number_input("Potência (cv) *", min_value=0.5,
                                     value=float(base["potencia_cv"] or 1), step=0.5)
        f_tensao = c2.selectbox("Tensão (V) *", TENSOES,
                                index=_indice(TENSOES, base["tensao_v"], 1))
        f_corrente = c3.number_input("Corrente Nominal (A) *", min_value=0.1,
                                     value=float(base["corrente_nominal_a"] or 1), step=0.1)
        f_fp = c4.slider("Fator de Potência", 0.60, 1.00,
                         value=float(base["fator_potencia"] or 0.86), step=0.01)

        st.markdown("### ⚙️ Parâmetros Mecânicos e Construtivos")
        c1, c2, c3, c4 = st.columns(4)
        f_rotacao = c1.number_input("Rotação (RPM) *", min_value=500,
                                    value=int(base["rotacao_rpm"] or 1760), step=10)
        f_classe = c2.selectbox("Classe de Isolamento", CLASSES_ISOLAMENTO,
                                index=_indice(CLASSES_ISOLAMENTO, base["classe_isolamento"], 2))
        f_ip = c3.selectbox("Grau de Proteção (IP)", IPS,
                            index=_indice(IPS, base["ip"], 3))
        f_peso = c4.number_input("Peso (kg)", min_value=1.0,
                                 value=float(base["peso_kg"] or 1), step=1.0)

        st.markdown("### 📍 Localização e Estado")
        c1, c2 = st.columns([3, 1])
        f_local = c1.text_input("Localização / Área", value=base["local"],
                                placeholder="Planta A — Linha 1")
        f_status = c2.selectbox("Status Operacional", STATUS,
                                index=_indice(STATUS, base["status"]))

        enviado = st.form_submit_button("💾 Salvar", type="primary")

    if not enviado:
        return

    # Validação local antes de gastar uma requisição.
    if not f_tag.strip() or not f_modelo.strip():
        st.error("TAG e Modelo são obrigatórios.")
        return

    sucesso, mensagem = pipeline.salvar_equipamento(
        f_tag, f_modelo, f_fabricante, f_potencia, f_tensao, f_corrente,
        f_rotacao, f_fp, f_classe, f_ip, f_peso, f_local, f_status,
    )

    if not sucesso:
        st.error(mensagem)
        return

    # A lista e a ficha precisam refletir o que acabou de ser gravado.
    api_provider.limpar_cache()
    st.session_state["_cadastro_aviso"] = mensagem
    app_state.ir_para("cadastro", tag=f_tag.strip().upper(), modo="edicao")
