# =============================================================================
# state/app_state.py — Estados compartilhados entre páginas e features
#
# Todos os gr.State da aplicação ficam aqui centralizados.
# Instanciar UMA VEZ dentro do contexto gr.Blocks() e passar para as features.
#
# Estados:
#   pagina_atual:    página visível no momento ("home" | "cadastro" | "dados")
#   tag_selecionada: TAG do equipamentos em foco (vazio = novo cadastro)
#   modo_cadastro:   como a tela de Cadastro foi aberta
#                    "novo"   = formulário em branco
#                    "edicao" = pré-preenchido com tag_selecionada
# =============================================================================

import gradio as gr


class AppState:
    """
    Contêiner de todos os gr.State da aplicação.
    Deve ser instanciado UMA VEZ dentro do contexto gr.Blocks().
    """

    def __init__(self):
        # Página atualmente visível — controla qual gr.Column está visible=True
        self.pagina_atual = gr.State("equipamentos")

        # TAG do equipamentos selecionado — vazio quando é um novo cadastro
        self.tag_selecionada = gr.State("")

        # Modo de abertura da tela de Cadastro:
        #   "novo"   → abre com formulário limpo (botão "Novo Equipamentos")
        #   "edicao" → abre pré-preenchido (clique em "Ver Ficha Técnica")
        self.modo_cadastro = gr.State("novo") 

        self.gatilho_cadastro = gr.State({"tag": "", "modo": "novo"})        
