# =============================================================================
# features/equipamentos/page.py — Tela inicial: listagem de equipamentos
#
# Seleção de linha: st.dataframe com on_select="rerun" devolve os índices
# das linhas marcadas pelo usuário. É o equivalente ao .select() do
# gr.Dataframe, com a diferença de que aqui não registramos callback —
# lemos o retorno do próprio componente.
# =============================================================================

import streamlit as st

import pipelines.cadastro_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state


def render() -> None:
    st.markdown("## 📋 Equipamentos Cadastrados")

    col_novo, col_atualizar, _ = st.columns([1, 1, 4])

    if col_novo.button("➕ Novo Equipamento", type="primary", width="stretch"):
        app_state.ir_para("cadastro", tag="", modo="novo")

    if col_atualizar.button("🔄 Atualizar Lista", width="stretch"):
        api_provider.limpar_cache()
        st.rerun()

    df = pipeline.listar_para_tabela()

    erro = api_provider.ultimo_erro()
    if erro:
        st.error(erro)

    if df.empty:
        st.warning("Nenhum equipamento retornado pela API. Verifique se o back-end está no ar.")
        return

    st.caption("Selecione uma linha na tabela e use os botões abaixo para navegar.")

    selecao = st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        on_select="rerun",          # cada clique reexecuta o script com a seleção
        selection_mode="single-row",
        key="tabela_equipamentos",
    )

    linhas = selecao.selection.rows
    tag = df.iloc[linhas[0]]["TAG"] if linhas else ""

    col_ficha, col_dados, col_dash = st.columns(3)

    # disabled=not tag: sem linha selecionada, as ações ficam inativas
    if col_ficha.button("📝 Ver Ficha Técnica", type="primary",
                        width="stretch", disabled=not tag):
        app_state.ir_para("cadastro", tag=tag, modo="edicao")

    if col_dados.button("📡 Ver Dados de Sensores",
                        width="stretch", disabled=not tag):
        app_state.ir_para("dados", tag=tag)

    if col_dash.button("📊 Ver no Dashboard",
                       width="stretch", disabled=not tag):
        app_state.ir_para("dashboard", tag=tag)

    if tag:
        st.success(f"Equipamento **{tag}** selecionado.")
    else:
        st.info("Selecione uma linha para habilitar as ações acima.")
