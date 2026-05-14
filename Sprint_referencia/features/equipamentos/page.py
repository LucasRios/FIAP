# =============================================================================
# features/equipamentos/page.py — Tela inicial: listagem de equipamentos
#
# Mudanças nesta versão:
#   - Botão "Novo Equipamento" (abre Cadastro em modo "novo")
#   - Botão "Atualizar Lista" ao lado do Novo
#   - Tabela com duas primeiras colunas de ação:
#       Col 1 → "Ver Ficha" (abre Cadastro em modo "edicao" com a TAG)
#       Col 2 → "Ver Dados" (abre Dados de Sensores com a TAG)
#   - Remoção do dropdown de seleção — a ação vem da tabela
# =============================================================================

import gradio as gr

import pipelines.cadastro_pipeline as pipeline
import providers.equipamento_provider as eq_provider
from state.app_state import AppState


def criar_pagina(state: AppState) -> None:

    gr.Markdown("## 📋 Equipamentos Cadastrados")

    # ── Barra de ações ──────────────────────────────────────────────────────
    with gr.Row():
        botao_novo      = gr.Button("➕ Novo Equipamento", variant="primary",   scale=1)
        botao_atualizar = gr.Button("🔄 Atualizar Lista",  variant="secondary", scale=1)
        gr.Column(scale=4)  # empurra os botões para a esquerda

    # ── Tabela de equipamentos ──────────────────────────────────────────────
    # A tabela inclui duas colunas de ação no início.
    # O usuário seleciona a linha desejada e usa os botões abaixo da tabela
    # para navegar — gr.Dataframe não suporta botões inline por linha.
    gr.Markdown(
        "_Selecione uma linha na tabela e use os botões abaixo para navegar._"
    )

    tabela = gr.Dataframe(
        value=pipeline.listar_para_tabela(),
        headers=pipeline.COLUNAS_TABELA,
        interactive=False,
        label="Ativos cadastrados",
    )

    # ── Ações sobre a linha selecionada ─────────────────────────────────────
    # gr.Dataframe expõe a linha selecionada via .select() — capturamos
    # a TAG (primeira coluna) para passar ao estado compartilhado.
    tag_linha = gr.State("")  # TAG da linha atualmente selecionada na tabela

    with gr.Row():
        botao_ficha = gr.Button("📝 Ver Ficha Técnica",     variant="primary",   scale=1)
        botao_dados = gr.Button("📡 Ver Dados de Sensores", variant="secondary", scale=1)

    msg_selecao = gr.Textbox(
        label="",
        interactive=False,
        show_label=False,
        placeholder="Selecione uma linha para habilitar as ações acima",
    )

    # ── Eventos ────────────────────────────────────────────────────────────

    # Captura a linha clicada na tabela e salva a TAG no state local
    def _selecionar_linha(evt: gr.SelectData):
        """
        Disparado quando o usuário clica em qualquer célula da tabela.
        evt.index = [linha, coluna] — pegamos a linha para buscar a TAG.
        evt.value = valor da célula clicada.

        A TAG está sempre na primeira coluna (índice 0).
        Precisamos remontar a lista e pegar o valor correto.
        """
        # evt.index[0] = índice da linha clicada
        linha_idx = evt.index[0]
        dados = pipeline.listar_para_tabela()

        if linha_idx >= len(dados):
            return "", "Seleção inválida."

        tag = dados[linha_idx][0]  # TAG é a primeira coluna
        return tag, f"✅ Equipamento **{tag}** selecionado."

    tabela.select(
        fn=_selecionar_linha,
        outputs=[tag_linha, msg_selecao],
    )

    # Botão "Novo Equipamento": limpa a TAG, define modo "novo", navega para Cadastro
    botao_novo.click(
        fn=lambda: {"tag": "", "modo": "novo"},
        outputs=state.gatilho_cadastro,        # ← escreve gatilho ANTES
    ).then(
        fn=lambda: "cadastro",
        outputs=state.pagina_atual,            # ← depois navega
    )

    # Botão "Ver Ficha Técnica": passa a TAG da linha, define modo "edicao", navega
    botao_ficha.click(
        fn=lambda tag: {"tag": tag, "modo": "edicao"},
        inputs=tag_linha,
        outputs=state.gatilho_cadastro,        # ← escreve gatilho ANTES
    ).then(
        fn=lambda: "cadastro",
        outputs=state.pagina_atual,            # ← depois navega
    )   

    # Botão "Ver Dados de Sensores": passa a TAG da linha, navega para Dados
    botao_dados.click(
        fn=lambda tag: tag,
        inputs=tag_linha,
        outputs=state.tag_selecionada,
    ).then(
        fn=lambda: "dados",
        outputs=state.pagina_atual,
    )

    # Botão "Atualizar Lista": recarrega a tabela com dados frescos do provider
    botao_atualizar.click(
        fn=pipeline.listar_para_tabela,
        outputs=tabela,
    )
