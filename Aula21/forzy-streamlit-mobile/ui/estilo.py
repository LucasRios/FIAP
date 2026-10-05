# =============================================================================
# ui/estilo.py — Camada opcional de CSS (nível avançado)
#
# O nível nativo (tema + componentes) já entrega um app usável no celular.
# Este arquivo resolve o que os parâmetros do Streamlit não alcançam:
#
#   1. alvos de toque de 48 px (os botões nativos medem 40 px; os da
#      navegação, 32 px);
#   2. navegação fixa na base da tela, na zona do polegar, só no celular;
#   3. botão "Salvar" sempre visível em formulários longos;
#   4. borda lateral colorida no resumo, reforçando a severidade;
#   5. respeito à preferência do sistema por menos movimento.
#
# REGRA DE OURO: prefira os ganchos documentados. Todo container ou widget
# com `key="x"` recebe a classe CSS `st-key-x` — esse é o contrato público.
# Seletores como [data-testid="..."] são INTERNOS: funcionam hoje e podem
# quebrar na próxima versão. Aqui há um só, isolado e comentado.
# =============================================================================

import streamlit as st

from ui.tokens import BREAKPOINT, TOQUE, cores


def _css(modo: str) -> str:
    """Folha de estilo gerada a partir dos tokens — nenhuma cor escrita à mão."""
    t = cores(modo)
    compacto = BREAKPOINT["compacto_px"] - 1
    return f"""
<style>
:root {{
  --fz-fundo: {t['fundo']};
  --fz-texto: {t['texto']};
  --fz-borda-suave: {t['borda_suave']};
  --fz-normal: {t['normal_destaque']};
  --fz-aviso: {t['aviso_destaque']};
  --fz-critico: {t['critico_destaque']};
  --fz-alvo: {TOQUE['alvo_minimo_px']}px;
  --fz-nav: 64px;
}}

/* 1. Alvos de toque: só nos NOSSOS containers de ação e na navegação */
.st-key-nav_principal button,
[class*="st-key-acoes"] button {{
  min-height: var(--fz-alvo);
}}

/* Destino ativo: o Streamlit usa a cor primária como cor de TEXTO aqui, e no
   modo escuro nenhum azul tem contraste 4,5:1 ao mesmo tempo contra o fundo
   escuro e contra o texto branco do botão. Texto padrão + peso maior resolve,
   e o peso vira um segundo sinal além da cor. */
.st-key-nav_principal [aria-checked="true"] {{
  color: var(--fz-texto) !important;
  font-weight: 600;
}}

/* 4. Severidade reforçada por uma borda lateral (forma + cor, nunca só cor) */
.st-key-resumo_normal  {{ border-left: 6px solid var(--fz-normal)  !important; }}
.st-key-resumo_aviso   {{ border-left: 6px solid var(--fz-aviso)   !important; }}
.st-key-resumo_critico {{ border-left: 6px solid var(--fz-critico) !important; }}

/* Classe de janela compacta (celular em retrato) */
@media (max-width: {compacto}px) {{

  /* SELETOR INTERNO — pode mudar entre versões do Streamlit.
     O padrão é 96 px de respiro no topo: num celular, 11% da tela vazia. */
  [data-testid="stMainBlockContainer"] {{
    padding-top: 0.75rem;
    padding-bottom: calc(var(--fz-nav) + 32px + env(safe-area-inset-bottom));
  }}

  /* 2. Navegação na base, na zona do polegar */
  .st-key-nav_principal {{
    position: fixed;
    left: 0; right: 0; bottom: 0;
    z-index: 1000;
    background: var(--fz-fundo);
    border-top: 1px solid var(--fz-borda-suave);
    padding: 8px 12px calc(8px + env(safe-area-inset-bottom));
  }}

  /* 3. "Salvar" acompanha a rolagem do formulário, logo acima da navegação.
     O sticky vai no PAI do nosso container: o Streamlit embrulha cada bloco
     num wrapper do mesmo tamanho, e um elemento sticky só se move dentro do
     pai. O :has() mantém a âncora na nossa classe pública, sem citar nomes
     internos — mas ainda depende da estrutura existir. */
  div:has(> .st-key-acoes_cadastro) {{
    position: sticky;
    bottom: calc(var(--fz-nav) + env(safe-area-inset-bottom));
    background: var(--fz-fundo);
    padding: 8px 0;
    z-index: 10;
  }}
}}

/* 5. Quem pediu ao sistema operacional menos animação, recebe menos animação */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def aplicar_estilo(modo: str = "light") -> None:
    """
    Injeta o CSS. Chamado uma vez por execução, no app.py.

    st.html com apenas <style> não cria elemento visível: o Streamlit aplica a
    folha de estilo sem ocupar espaço na página.
    """
    st.html(_css(modo))
