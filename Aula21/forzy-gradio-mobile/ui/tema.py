# =============================================================================
# ui/tema.py — Os tokens do Forzy traduzidos para o Gradio
#
# NÍVEL 1 (nativo): criar_tema() — o tema do Gradio É um sistema de tokens,
# com mais de 300 variáveis, todas com variante clara e escura (sufixo _dark).
# Aqui cada variável recebe um token semântico de ui/tokens.py.
#
# NÍVEL 2 (avançado): CSS_GLOBAL — o que o tema não alcança: navegação na
# base da tela no celular e alvos de toque de 48 px.
#
# No Gradio 6, tema e CSS são passados ao launch(), e não mais ao gr.Blocks().
# =============================================================================

import gradio as gr

from ui.tokens import BREAKPOINT, RAIO, TOQUE, cores

# Fontes do sistema: nenhum download. Num galpão com sinal ruim, uma fonte
# baixada da internet é mais um recurso que pode atrasar a primeira tela.
FONTE_SISTEMA = ["system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"]


def criar_tema() -> gr.themes.Base:
    """Tema Gradio gerado a partir dos tokens, nos modos claro e escuro."""
    c, e = cores("claro"), cores("escuro")
    return gr.themes.Base(
        neutral_hue="slate",
        radius_size=gr.themes.sizes.radius_md,
        font=FONTE_SISTEMA,
        font_mono=["ui-monospace", "Consolas", "monospace"],
    ).set(
        body_background_fill=c["fundo"], body_background_fill_dark=e["fundo"],
        body_text_color=c["texto"], body_text_color_dark=e["texto"],
        body_text_color_subdued=c["texto_suave"], body_text_color_subdued_dark=e["texto_suave"],
        body_text_size="16px",                          # nunca menos: o iOS dá zoom em campos < 16 px
        background_fill_primary=c["fundo"], background_fill_primary_dark=e["fundo"],
        background_fill_secondary=c["superficie"], background_fill_secondary_dark=e["superficie"],
        block_background_fill=c["fundo"], block_background_fill_dark=e["fundo"],
        block_border_color=c["borda_suave"], block_border_color_dark=e["borda_suave"],
        border_color_primary=c["borda_suave"], border_color_primary_dark=e["borda_suave"],
        input_border_color=c["borda"], input_border_color_dark=e["borda"],   # 3:1: campo visível ao sol
        input_border_width="1px",
        # No tema Base, a borda do botão herda a do campo, que é ZERO: o botão
        # secundário ficava sem contorno — texto solto que não parece tocável.
        button_border_width="1px",
        color_accent=c["acao"], color_accent_soft=c["superficie"], color_accent_soft_dark=e["superficie"],
        # A cor da AÇÃO é azul: o laranja padrão do Gradio (texto branco a 2,8:1)
        # reprovava no contraste e ainda disputava com o âmbar do AVISO.
        button_primary_background_fill=c["acao"], button_primary_background_fill_dark=e["acao"],
        button_primary_background_fill_hover=c["acao"], button_primary_background_fill_hover_dark=e["acao"],
        button_primary_text_color=c["texto_sobre_acao"], button_primary_text_color_dark=e["texto_sobre_acao"],
        button_primary_border_color=c["acao"], button_primary_border_color_dark=e["acao"],
        button_secondary_background_fill=c["fundo"], button_secondary_background_fill_dark=e["fundo"],
        button_secondary_text_color=c["texto"], button_secondary_text_color_dark=e["texto"],
        button_secondary_border_color=c["borda"], button_secondary_border_color_dark=e["borda"],
        button_large_padding="12px 20px",               # com texto de 16 px, chega a 48 px de altura
        button_large_text_size="16px",
        button_large_radius=f"{RAIO['sm']}px",
        loader_color=c["acao"], loader_color_dark=e["acao"],
    )


def _variaveis_css() -> str:
    """Tokens como variáveis CSS, nos dois modos — usadas pelos templates."""
    def bloco(t: dict) -> str:
        return "".join(f"--fz-{k.replace('_', '-')}: {v};" for k, v in t.items())
    return f":root {{ {bloco(cores('claro'))} --fz-alvo: {TOQUE['alvo_minimo_px']}px; }}\n.dark {{ {bloco(cores('escuro'))} }}"


CSS_GLOBAL = _variaveis_css() + f"""
/* Alvos de toque: botões e abas com no mínimo 48 px */
#nav [role="tab"], .fz-acoes button {{ min-height: var(--fz-alvo); }}

/* Celular (classe compacta < {BREAKPOINT['compacto_px']} px) */
@media (max-width: {BREAKPOINT['compacto_px'] - 1}px) {{
  /* Navegação na base da tela, na zona do polegar.
     [role="tablist"] é um papel de ACESSIBILIDADE: um contrato bem mais
     estável que os nomes de classe internos do Gradio. */
  #nav [role="tablist"] {{
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 1000;
    display: flex; background: var(--fz-fundo);
    border-top: 1px solid var(--fz-borda-suave);
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
  }}
  #nav [role="tab"] {{ flex: 1; justify-content: center; }}

  /* Registro de ocorrência como "folha" que sobe da base (bottom sheet):
     a tarefa curta acontece sobre o contexto, sem trocar de tela. */
  .fz-folha {{
    position: fixed; left: 0; right: 0; z-index: 1001;
    bottom: calc(64px + env(safe-area-inset-bottom));
    max-height: 75dvh; overflow-y: auto;
    background: var(--fz-fundo); border-top: 1px solid var(--fz-borda);
    border-radius: {RAIO['lg']}px {RAIO['lg']}px 0 0;
    box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.18);
    padding: 16px;
  }}
  .gradio-container {{ padding-bottom: calc(96px + env(safe-area-inset-bottom)) !important; }}
  /* SELETOR INTERNO — pode mudar entre versões do Gradio.
     O padrão são 32 px de margem lateral: no celular, 16% da largura útil. */
  .gradio-container main.app {{ padding-left: 12px !important; padding-right: 12px !important; }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
"""
