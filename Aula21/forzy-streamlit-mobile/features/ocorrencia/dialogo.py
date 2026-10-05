# =============================================================================
# features/ocorrencia/dialogo.py — Registro de ocorrência (human-in-the-loop)
#
# O operador registra o que os sensores sozinhos não captam. No celular, de
# luva, digitar é a parte mais cara da tarefa — por isso as ocorrências mais
# comuns viram pílulas de um toque, e o texto livre é opcional.
#
# Aparece como diálogo modal: a tarefa é curta e focada, e o contexto (o
# painel do motor) continua por trás, sem trocar de página.
# =============================================================================

from datetime import datetime

import streamlit as st

TIPOS_COMUNS = ["Ruído anormal", "Aquecimento", "Vibração", "Vazamento", "Cheiro de queimado", "Outro"]


@st.dialog("Registrar ocorrência", icon=":material/edit_note:")
def dialogo_ocorrencia(tag: str) -> None:
    """Formulário curto: tipo por toque, detalhe opcional, um botão grande."""
    st.caption(f"Motor **{tag}**")
    tipos = st.pills("O que você observou?", TIPOS_COMUNS, selection_mode="multi", key="oc_tipos")
    detalhe = st.text_area("Detalhes (opcional)", placeholder="Ex.: ruído metálico só sob carga máxima",
                           height=96, key="oc_detalhe")

    if st.button("Registrar", type="primary", icon=":material/check:", width="stretch"):
        if not tipos and not detalhe.strip():
            st.error("Escolha ao menos um tipo ou descreva a ocorrência.")
            return
        # Em produção: POST /v1/ocorrencias no back-end.
        hora = datetime.now().strftime("%H:%M")
        st.session_state["_aviso_global"] = f"Ocorrência registrada para {tag} às {hora}."
        st.rerun()  # fecha o diálogo
