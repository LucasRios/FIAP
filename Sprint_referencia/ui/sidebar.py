# =============================================================================
# ui/sidebar.py — Componente de navegação lateral (sidebar)
#
# Por que separar em ui/?
# ------------------------
# O sidebar é um componente de UI puro — não conhece lógica de negócio
# nem pipelines. Isolá-lo em ui/ permite:
#   1. Reutilizá-lo em outros projetos sem arrastar dependências
#   2. Alterar o visual do menu sem tocar no app.py
#   3. Documentar claramente o que é "casca" (UI) e o que é "núcleo" (lógica)
#
# Como usar no app.py:
#   from ui.sidebar import criar_sidebar
#   botoes = criar_sidebar()          # cria o componente dentro do gr.Blocks
#   botoes["equipamentos"].click(...)         # acessa os botões pelo nome
#
# O que este módulo NÃO faz:
#   - Não conhece gr.State
#   - Não registra eventos (isso é responsabilidade do app.py)
#   - Não importa nada das features ou pipelines
# =============================================================================

import gradio as gr


def criar_sidebar(open: bool = True) -> dict[str, gr.Button]:
    """
    Cria o gr.Sidebar com os botões de navegação.

    Deve ser chamada DENTRO de um contexto gr.Blocks() já aberto.

    Parâmetro:
        open: se True, a sidebar começa expandida (padrão).

    Retorna um dicionário com os botões de navegação:
        {
            "equipamentos":  gr.Button,   # 🏠 Equipamentos
            "dados": gr.Button,   # 📡 Dados de Sensores
        }

    O app.py usa esse dicionário para registrar os eventos .click()
    em cada botão — mantendo a lógica de navegação fora deste componente.

    Nota: Cadastro Técnico não aparece no menu — é acessado apenas
    a partir da tela de Equipamentos (novo ou edição).
    """

    with gr.Sidebar(open=open, width=220):

        gr.Markdown("## ⚙️ Forzy")
        gr.Markdown("_Digital Twin · Motores_")
        gr.Markdown("---")
        gr.Markdown("**Navegação**")

        # Botão equipamento — variant="primary" porque é a página inicial (ativa por padrão)
        btn_equipamento  = gr.Button("🏠  Equipamentos",     variant="primary",   size="sm")

        # Cadastro Técnico removido do menu intencionalmente:
        # o acesso se dá pelos botões "Novo" e "Ver Ficha Técnica" na equipamentos.

        # Dados de Sensores — acessível diretamente pelo menu
        btn_dados = gr.Button("📡  Dados de Sensores", variant="secondary", size="sm")

        gr.Markdown("---")
        gr.Markdown("_Sprint 1 — Fundamentos_")

    # Retorna apenas os botões que o app.py precisa conectar a eventos
    return {
        "equipamentos":  btn_equipamento,
        "dados": btn_dados,
    }
