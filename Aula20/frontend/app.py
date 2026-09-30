# =============================================================================
# app.py — Ponto de entrada da aplicação
#
# Estrutura:
#   ui/sidebar.py       ← componente visual do menu (sem lógica)
#   state/app_state.py  ← gr.State compartilhados entre páginas
#   features/*/page.py  ← conteúdo de cada página
# =============================================================================

import gradio as gr

import features.equipamentos.page  as equipamento_page
import features.cadastro.page      as cadastro_page
import features.sensores.page      as dados_brutos_page
import features.dashboard.page     as dashboard_page       # Sprint 2

from state.app_state import AppState
from ui.sidebar      import criar_sidebar


with gr.Blocks(title="Forzy · Digital Twin") as app:

    state = AppState()

    # Sidebar: retorna os botões do menu para conectarmos os eventos abaixo
    botoes = criar_sidebar(open=True)

    # Cada página é uma coluna. Só uma fica visível por vez.
    # A página equipamento começa visível (visible=True); as demais ficam ocultas.
    with gr.Column(visible=True) as col_equipamento:
        equipamento_page.criar_pagina(state)

    with gr.Column(visible=False) as col_cadastro:
        cadastro_page.criar_pagina(state)

    with gr.Column(visible=False) as col_dados:
        dados_brutos_page.criar_pagina(state)

    with gr.Column(visible=False) as col_dashboard:      # Sprint 2
        dashboard_page.criar_pagina(state)

    # ── Navegação ───────────────────────────────────────────────────────────
    # A ideia: state.pagina_atual guarda qual página está ativa ("equipamento",
    # "cadastro" ou "dados"). Quando esse valor muda — seja pelo clique
    # num botão do menu, seja por um botão dentro de uma feature —
    # a função _navegar() é chamada e mostra a coluna correta.

    def _navegar(pagina: str):
        """
        Recebe o nome da página que deve ficar visível e retorna
        as atualizações necessárias para cada coluna e botão do menu.

        visible=True  → coluna aparece na tela
        visible=False → coluna some da tela

        variant="primary"   → botão do menu fica destacado (página ativa)
        variant="secondary" → botão do menu fica normal
        """

        # Decide qual coluna mostrar e quais esconder
        mostrar_equipamento = gr.update(visible = pagina == "equipamentos")
        mostrar_cadastro    = gr.update(visible = pagina == "cadastro")
        mostrar_dados       = gr.update(visible = pagina == "dados")
        mostrar_dashboard   = gr.update(visible = pagina == "dashboard")   # Sprint 2

        # Destaca o botão do menu que corresponde à página ativa
        # (Cadastro não tem botão no menu — é acessado pela equipamento)
        destacar_equipamento = gr.update(variant = "primary" if pagina in ("equipamentos", "cadastro") else "secondary")
        destacar_dados       = gr.update(variant = "primary" if pagina == "dados"      else "secondary")
        destacar_dashboard   = gr.update(variant = "primary" if pagina == "dashboard"  else "secondary")  # Sprint 2

        return mostrar_equipamento, mostrar_cadastro, mostrar_dados, mostrar_dashboard, destacar_equipamento, destacar_dados, destacar_dashboard

    # Conecta _navegar ao estado — dispara sempre que pagina_atual mudar
    state.pagina_atual.change(
        fn=_navegar,
        inputs=state.pagina_atual,
        outputs=[col_equipamento, col_cadastro, col_dados, col_dashboard,
                 botoes["equipamentos"], botoes["dados"], botoes["dashboard"]],
    )

    # Botões do menu: cada um escreve o nome da sua página em pagina_atual
    # O .change() acima cuida do resto automaticamente
    botoes["equipamentos"].click(fn=lambda: "equipamentos", outputs=state.pagina_atual)
    botoes["dados"].click(fn=lambda: "dados",               outputs=state.pagina_atual)
    botoes["dashboard"].click(fn=lambda: "dashboard",       outputs=state.pagina_atual)  # Sprint 2


# share=True cria um link público temporário (útil para testar em outro dispositivo).
# Para uso local em sala de aula, deixamos desligado por padrão.
app.launch(share=False, inbrowser=True)
