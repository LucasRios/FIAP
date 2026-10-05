# =============================================================================
# app.py — Ponto de entrada do Forzy (Gradio, versão mobile-first)
#
# Camadas (as mesmas da versão Streamlit):
#   ui/tokens.py        design tokens — arquivo IDÊNTICO ao do Streamlit
#   ui/tema.py          tokens → tema do Gradio + CSS global
#   ui/componentes.py   componentes: contrato de dados + dois níveis de desenho
#   state/app_state.py  pedido de navegação + deep link
#   features/*/page.py  telas: só orquestram
#   pipelines/          IDÊNTICAS às do Streamlit
#   providers/          única porta de saída para a API
#
# Navegação: gr.Tabs. No celular, o CSS avançado leva a barra de abas para a
# base da tela. A sidebar saiu: no celular ela cobria a tela inteira.
# =============================================================================

import os
from urllib.parse import urlencode

import gradio as gr

import features.cadastro.page as cadastro_page
import features.dashboard.page as dashboard_page
import features.equipamentos.page as equipamentos_page
import features.sensores.page as sensores_page
import providers.api_provider as api_provider
from state.app_state import AppState, pedido_da_url
from ui.componentes import AVANCADO
from ui.tema import CSS_GLOBAL, criar_tema

# A API no plano gratuito hiberna: acordá-la antes de montar a interface.
api_provider.acordar_api()

# Destino do pedido -> aba que deve ficar selecionada
ABA_DO_DESTINO = {"motores": "motores", "cadastro": "motores", "painel": "painel", "sensores": "sensores"}

# Mantém a URL igual à tela, para F5 e compartilhamento. Roda no NAVEGADOR.
# Ele não enxerga o gr.State (que mora no servidor); por isso o roteador
# escreve a query string num componente oculto, e é dele que este JS lê.
JS_URL = """(q) => {
  history.replaceState(null, '', location.pathname + (q ? '?' + q : ''));
}"""

# analytics_enabled=False: sem telemetria para api.gradio.app. Numa rede
# industrial restrita, cada chamada externa bloqueada é atraso na abertura.
with gr.Blocks(title="Forzy · Digital Twin", analytics_enabled=False) as app:
    state = AppState()

    gr.Markdown("**⚙️ Forzy** · Digital Twin · Motores", elem_id="barra-superior")
    url_atual = gr.Textbox(visible=False)  # ponte servidor -> navegador para a URL

    with gr.Tabs(selected="motores", elem_id="nav") as nav:
        with gr.Tab("Motores", id="motores"):
            with gr.Column() as col_lista:
                lista = equipamentos_page.criar_pagina(state)
            with gr.Column(visible=False) as col_cadastro:
                cadastro = cadastro_page.criar_pagina(state)
        with gr.Tab("Painel", id="painel"):
            painel = dashboard_page.criar_pagina()
        with gr.Tab("Sensores", id="sensores"):
            sensores = sensores_page.criar_pagina()

    # ── Roteador: a ÚNICA função que troca de tela ──────────────────────────
    def rotear(p: dict) -> list:
        destino, tag = p["destino"], p["tag"]
        saidas = [gr.Tabs(selected=ABA_DO_DESTINO[destino]),
                  gr.Column(visible=destino != "cadastro"),
                  gr.Column(visible=destino == "cadastro")]
        if destino == "cadastro":
            saidas += cadastro["abrir"](tag, p["modo"])
        else:
            saidas += [gr.skip()] * len(cadastro["saidas_abrir"])
        saidas.append(gr.Dropdown(value=tag) if destino == "painel" and tag else gr.skip())
        saidas.append(gr.Dropdown(value=tag) if destino == "sensores" and tag else gr.skip())
        saidas.append(urlencode({k: v for k, v in {"pagina": destino, "tag": tag}.items() if v}))
        return saidas

    state.navegar.change(
        rotear, inputs=state.navegar,
        outputs=[nav, col_lista, col_cadastro, *cadastro["saidas_abrir"],
                 painel["motor"], sensores["motor"], url_atual],
    )
    url_atual.change(fn=None, inputs=url_atual, js=JS_URL)

    # ── Abertura da página: dados frescos + deep link (?pagina=...&tag=...) ─
    def ao_abrir(request: gr.Request):
        opcoes = dashboard_page.opcoes_motores()
        return (gr.Dropdown(choices=opcoes), gr.Dropdown(choices=opcoes),
                gr.Radio(choices=api_provider.listar_plantas()), 1,
                pedido_da_url(dict(request.query_params)))

    app.load(ao_abrir, outputs=[painel["motor"], sensores["motor"], painel["planta"],
                                lista["recarregar"], state.navegar])


if __name__ == "__main__":
    # No Gradio 6, tema, CSS e cabeçalho vão no launch(), não no gr.Blocks().
    # O CSS global é parte do nível avançado: FORZY_CSS=0 desliga.
    # footer_links=[]: sem o rodapé "Built with Gradio", que no celular ficava
    # escondido atrás da navegação.
    # PORT: no Render (e em plataformas parecidas) a porta é definida pela
    # plataforma, e o servidor precisa escutar em 0.0.0.0. Localmente, sem
    # PORT, valem os padrões do Gradio (127.0.0.1:7860).
    porta = os.getenv("PORT")
    app.launch(theme=criar_tema(), css=CSS_GLOBAL if AVANCADO else None, footer_links=[],
               server_name="0.0.0.0" if porta else None,
               server_port=int(porta) if porta else None)
