import gradio as gr

import pipelines.cadastro_pipeline as pipeline
from state.app_state import AppState

FABRICANTES        = ["WEG", "Siemens", "ABB", "Nidec", "Voges", "Outro"]
CLASSES_ISOLAMENTO = ["A", "B", "F", "H"]
IPS                = ["IP21", "IP44", "IP54", "IP55", "IP65", "IP66"]
TENSOES            = [220, 380, 440, 480, 690]
STATUS             = ["Operacional", "Em Manutenção", "Desligado"]


def criar_pagina(state: AppState) -> None:

    gr.Markdown("## 🔧 Cadastro Técnico do Equipamento")

    # Botão Voltar — posicionado no topo, fora das abas, sempre visível
    botao_voltar = gr.Button("← Voltar para Equipamentos", variant="secondary", size="sm")

    gr.Markdown("---")

    # ── Abas ────────────────────────────────────────────────────────────────
    with gr.Tabs() as abas:

        # ── Aba 1: Ficha Técnica (somente leitura) ───────────────────────────
        with gr.TabItem("📄 Ficha Técnica", id=0):

            ficha = gr.Markdown(
                value="_Nenhum equipamento selecionado._"
            )

        # ── Aba 2: Edição ────────────────────────────────────────────────────
        with gr.TabItem("✏️ Edição", id=1):

            gr.Markdown("### Identificação")
            with gr.Row():
                f_tag        = gr.Textbox(label="TAG *",        placeholder="MTR-004")
                f_modelo     = gr.Textbox(label="Modelo *",     placeholder="WEG W22 160L")
                f_fabricante = gr.Dropdown(label="Fabricante *", choices=FABRICANTES)

            gr.Markdown("### ⚡ Parâmetros Elétricos")
            with gr.Row():
                f_potencia = gr.Number(label="Potência (cv) *",       minimum=0.5)
                f_tensao   = gr.Dropdown(label="Tensão (V) *",          choices=TENSOES, value=380)
                f_corrente = gr.Number(label="Corrente Nominal (A) *", minimum=0.1)
                f_fp       = gr.Slider(label="Fator de Potência",       minimum=0.6, maximum=1.0, step=0.01, value=0.86)

            gr.Markdown("### ⚙️ Parâmetros Mecânicos e Construtivos")
            with gr.Row():
                f_rotacao = gr.Number(label="Rotação (RPM) *",        value=1760, minimum=500)
                f_classe  = gr.Dropdown(label="Classe de Isolamento",  choices=CLASSES_ISOLAMENTO, value="F")
                f_ip      = gr.Dropdown(label="Grau de Proteção (IP)", choices=IPS, value="IP55")
                f_peso    = gr.Number(label="Peso (kg)",               minimum=1)

            gr.Markdown("### 📍 Localização e Estado")
            with gr.Row():
                f_local  = gr.Textbox(label="Localização / Área",  placeholder="Planta A — Linha 1", scale=3)
                f_status = gr.Dropdown(label="Status Operacional", choices=STATUS, value="Operacional", scale=1)

            gr.Examples(
                examples=[
                    ["MTR-004", "WEG W22 200L", "WEG",  50.0, 380, 80.0, 0.88, 1775, "F", "IP55", 280.0, "Planta B — Linha 3", "Operacional"],
                    ["MTR-005", "ABB M3BP 90L", "ABB",   3.0, 220, 10.2, 0.80, 1720, "H", "IP66",  28.0, "Utilidades",          "Desligado"],
                ],
                inputs=[f_tag, f_modelo, f_fabricante, f_potencia, f_tensao,
                        f_corrente, f_fp, f_rotacao, f_classe, f_ip, f_peso, f_local, f_status],
                label="Exemplos de preenchimento",
            )

            _campos = [f_tag, f_modelo, f_fabricante, f_potencia, f_tensao,
                       f_corrente, f_fp, f_rotacao, f_classe, f_ip, f_peso, f_local, f_status]

            with gr.Row():
                botao_salvar = gr.Button("💾 Salvar", variant="primary",   scale=2)
                botao_limpar = gr.Button("🗑️ Limpar", variant="secondary", scale=1)

            msg_salvar = gr.Textbox(label="", interactive=False, show_label=False)

    # ── Funções auxiliares ──────────────────────────────────────────────────

    def _valores_limpos():
        """Valores padrão para o formulário em branco (modo "novo")."""
        return ["", "", None, None, 380, None, 0.86, 1760, "F", "IP55", None, "", "Operacional"]

    def _preencher_campos(tag: str):
        """Retorna valores do equipamento para popular os campos do formulário."""
        eq = pipeline.carregar_equipamento(tag.strip().upper())
        if not eq:
            return _valores_limpos()
        return [
            eq["tag"], eq["modelo"], eq["fabricante"],
            eq["potencia_cv"], eq["tensao_v"], eq["corrente_nominal_a"],
            eq["fator_potencia"], eq["rotacao_rpm"],
            eq["classe_isolamento"], eq["ip"], eq["peso_kg"],
            eq["local"], eq["status"],
        ]

    def _salvar(*campos):
        """Salva e atualiza a ficha técnica na aba 1."""
        mensagem = pipeline.salvar_equipamento(*campos)
        ficha_md = pipeline.ficha_tecnica_markdown(campos[0]) if mensagem.startswith("✅") else gr.update()
        return mensagem, ficha_md

    # ── Reação ao estado compartilhado ─────────────────────────────────────
    # Quando state.modo_cadastro ou state.tag_selecionada mudam
    # (porque a equipamento navegou para cá), reagimos abrindo a aba correta
    # e carregando os dados.

    def _abrir_pagina(tag: str, modo: str):
        
        if modo == "novo" or not tag:
            return (
                gr.update(selected=1),      # abre aba Edição
                "_Preencha os campos e salve para criar a ficha técnica._",
                *_valores_limpos(),
                "",                          # limpa msg_salvar
            )

        # modo "edicao": carrega dados da TAG
        ficha_md  = pipeline.ficha_tecnica_markdown(tag)
        campos    = _preencher_campos(tag)
        return (
            gr.update(selected=0),          # abre aba Ficha Técnica
            ficha_md,
            *campos,
            "",                              # limpa msg_salvar
        )

    # outputs: abas, ficha, 13 campos do formulário, msg_salvar
    _outputs_abrir = [abas, ficha] + _campos + [msg_salvar]

    # Dispara quando modo_cadastro muda (a tag_selecionada já foi escrita antes
    # pelo .then() encadeado na equipamento, então chegam juntos na prática)
    def _ao_navegar_para_cadastro(pagina: str, tag: str, modo: str):
        # Se não estamos indo para cadastro, não faz nada
        if pagina != "cadastro":
            return

        # Estamos indo para cadastro — carrega a página corretamente
        return _abrir_pagina(tag, modo)

    state.gatilho_cadastro.change(
        fn=lambda g: _abrir_pagina(g["tag"], g["modo"]),
        inputs=state.gatilho_cadastro,
        outputs=_outputs_abrir,
    )

    # ── Eventos locais ─────────────────────────────────────────────────────

    botao_salvar.click(
        fn=_salvar,
        inputs=_campos,
        outputs=[msg_salvar, ficha],
    ).then(
        # Após salvar com sucesso, atualiza a ficha e muda para a aba de visualização
        fn=lambda msg, _ficha: gr.update(selected=0) if msg.startswith("✅") else gr.update(),
        inputs=[msg_salvar, ficha],
        outputs=abas,
    )

    botao_limpar.click(fn=_valores_limpos, outputs=_campos)

    # Botão Voltar: navega para equipamento sem alterar a TAG
    botao_voltar.click(
        fn=lambda: "equipamentos",
        outputs=state.pagina_atual,
    )