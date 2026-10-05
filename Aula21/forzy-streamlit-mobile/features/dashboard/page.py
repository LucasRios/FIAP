# =============================================================================
# features/dashboard/page.py — Painel de um motor
#
# Reorganizado em "status primeiro":
#   1. escolha do motor — busca direta, com filtro por planta/área em pílulas
#   2. resumo — o motor está bem? (severidade + frase explicando o porquê)
#   3. grade de grandezas — cinco cards com tendência em miniatura
#   4. detalhe — UM gráfico por vez, escolhido por toque
#   5. placa — sob demanda, recolhida
#   6. ação — registrar ocorrência (human-in-the-loop)
# =============================================================================

import streamlit as st

import pipelines.dashboard_pipeline as pipeline
import providers.api_provider as api_provider
from features.ocorrencia.dialogo import dialogo_ocorrencia
from pipelines.formatacao import GRANDEZAS
from state import app_state
from ui import componentes as ui


def _escolher_motor() -> str | None:
    """
    Seleção do motor em no máximo dois toques.

    O caminho principal é um seletor com busca (digitar "07" já encontra o
    MTR-007). A hierarquia Planta → Área continua disponível como filtro em
    pílulas: alvos grandes, opções visíveis, sem abrir menus.
    """
    with st.expander("Filtrar por planta e área", icon=":material/filter_list:"):
        planta = st.pills("Planta", api_provider.listar_plantas(), key="filtro_planta")
        area = st.pills("Área", api_provider.listar_areas(planta) if planta else [],
                        key="filtro_area") if planta else None

    if planta and area:
        tags = api_provider.listar_equipamentos(planta, area)
    elif planta:
        tags = [t for a in api_provider.listar_areas(planta) for t in api_provider.listar_equipamentos(planta, a)]
    else:
        tags = api_provider.tags_disponiveis()

    if not tags:
        return None

    # Um único GET traz o local de todos os motores. Chamar buscar_localizacao()
    # dentro do format_func faria uma requisição POR OPÇÃO — o problema N+1.
    locais = {e["tag"]: e["local"] for e in api_provider.listar_todos()}

    atual = app_state.tag_selecionada()
    tag = st.selectbox(
        "Motor", tags, index=tags.index(atual) if atual in tags else 0,
        format_func=lambda t: f"{t} · {locais.get(t, '')}",
        key=f"motor_{atual}",
    )
    if tag != atual:
        st.session_state["tag_selecionada"] = tag
        st.query_params["tag"] = tag
    return tag


def render() -> None:
    ui.titulo_tela("Painel do motor")

    tag = _escolher_motor()
    if not tag:
        ui.estado_erro("Não foi possível carregar a lista de motores. Verifique se a API está no ar.")
        return

    p = pipeline.painel(tag)
    if not p:
        ui.estado_erro(f"Não foi possível obter os dados de {tag}.")
        return

    ui.resumo_motor(p)

    with st.container(horizontal=True, gap="small", key="acoes_painel"):
        if st.button("Registrar ocorrência", icon=":material/edit_note:", type="primary", width="stretch"):
            dialogo_ocorrencia(tag)
        if st.button("Atualizar", icon=":material/refresh:", width="stretch"):
            api_provider.limpar_cache()
            st.rerun()

    ui.espaco("sm")
    st.markdown("**Grandezas agora**")
    ui.grade_grandezas(p["grandezas"])

    ui.espaco("sm")
    st.markdown("**Últimas 24 horas**")
    chave = st.segmented_control(
        "Grandeza", options=list(GRANDEZAS), format_func=lambda c: GRANDEZAS[c]["nome"],
        default=p["grandeza_destaque"], required=True, key=f"grandeza_{tag}",
        label_visibility="collapsed", width="stretch",
    )
    fig = pipeline.grafico_grandeza(tag, chave, st.context.theme.type or "light")
    if fig is None:
        ui.estado_vazio("Sem histórico para este motor.")
    else:
        # Sem barra de ferramentas e sem zoom: no toque, ela só atrapalha a rolagem.
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

    with st.expander("Placa de identificação", icon=":material/badge:"):
        ui.pares_rotulo_valor(pipeline.placa(tag))
