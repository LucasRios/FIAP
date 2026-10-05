# =============================================================================
# ui/componentes.py — Componentes do design system do Forzy (Gradio)
#
# Um componente aqui é um CONTRATO DE DADOS com duas formas de desenho:
#
#   NÍVEL 1 (nativo)    o dado vira Markdown e é exibido num gr.Markdown.
#                       Forma e texto já carregam o significado (▲ Aviso).
#   NÍVEL 2 (avançado)  o dado vai CRU para um gr.HTML com html_template e
#                       css_template (Gradio 6). O template é Handlebars: ele
#                       escapa todo o conteúdo — um nome vindo da API com
#                       <script> aparece como texto, nunca executa.
#
# As páginas não sabem qual nível está ativo: chamam COMPONENTE.criar() para
# montar a saída e COMPONENTE.valor(dados) para preenchê-la.
# FORZY_CSS=0 liga só o nível nativo.
# =============================================================================

import os
import re

import gradio as gr

from ui.tokens import ESPACO, RAIO, severidade

AVANCADO = os.getenv("FORZY_CSS", "1") == "1"


def _md(texto) -> str:
    """Escapa caracteres de Markdown em dados vindos da API."""
    return re.sub(r"([\\`*_{}\[\]()#+!|<>~])", r"\\\1", str(texto))


def _sparkline(serie: list[float]) -> str:
    """Pontos de uma polyline SVG (caixa 100 x 28) para a tendência em miniatura."""
    if len(serie) < 2:
        return ""
    menor, maior = min(serie), max(serie)
    faixa = (maior - menor) or 1
    passo = 100 / (len(serie) - 1)
    return " ".join(f"{i * passo:.1f},{26 - (v - menor) / faixa * 24:.1f}" for i, v in enumerate(serie))


def _com_severidade(d: dict, chave: str = "severidade") -> dict:
    """Acrescenta forma e rótulo da severidade (vindos dos tokens) a um item."""
    if not d.get(chave):
        return d
    s = severidade(d[chave])
    return {**d, "simbolo": s["simbolo"], "rotulo": s["rotulo"]}


class Componente:
    """Um contrato de dados + duas maneiras de desenhá-lo."""

    def __init__(self, template: str, css: str, para_markdown, preparar=lambda d: d):
        self.template, self.css = template, css
        self.para_markdown, self.preparar = para_markdown, preparar

    def criar(self, value=None, **kwargs):
        """Cria a saída do componente: gr.HTML com template (avançado) ou gr.Markdown (nativo)."""
        if AVANCADO:
            return gr.HTML(value=value, html_template=self.template, css_template=self.css,
                           padding=False, container=False, apply_default_css=False, **kwargs)
        return gr.Markdown(value=value or "", **kwargs)

    def valor(self, dados):
        if dados is None:
            return None if AVANCADO else ""
        pronto = self.preparar(dados)
        return pronto if AVANCADO else self.para_markdown(pronto)


# Estilos que vários templates compartilham: o selo de severidade.
_CSS_SELO = f"""
.selo {{ display:inline-flex; align-items:center; gap:4px; padding:2px 10px;
        border-radius:{RAIO['pilula']}px; font-size:0.875rem; font-weight:600; }}
.selo.sev-normal  {{ color:var(--fz-normal-texto);  background:var(--fz-normal-fundo); }}
.selo.sev-aviso   {{ color:var(--fz-aviso-texto);   background:var(--fz-aviso-fundo); }}
.selo.sev-critico {{ color:var(--fz-critico-texto); background:var(--fz-critico-fundo); }}
.selo.sev-sem_dado{{ color:var(--fz-neutro-texto);  background:var(--fz-neutro-fundo); }}
"""

# ---------------------------------------------------------------------------
# RESUMO — "o status primeiro"
# ---------------------------------------------------------------------------
RESUMO = Componente(
    template="""
{{#if value}}
<section class="resumo sev-{{value.severidade}}" aria-label="Resumo do motor {{value.tag}}">
  <header>
    <h3>{{value.tag}}</h3>
    <span class="selo sev-{{value.severidade}}"><span aria-hidden="true">{{value.simbolo}}</span>{{value.rotulo}}</span>
  </header>
  <p class="explicacao">{{value.explicacao}}</p>
  <p class="meta">{{value.titulo}} · {{value.local}}<br>Leitura das {{value.hora}}</p>
  <span class="status">{{value.status_operacional}}</span>
</section>
{{/if}}""",
    css=_CSS_SELO + f"""
.resumo {{ border:1px solid var(--fz-borda); border-left-width:6px; border-radius:{RAIO['md']}px;
          padding:{ESPACO['lg']}px; display:flex; flex-direction:column; gap:{ESPACO['sm']}px; }}
.resumo.sev-normal  {{ border-left-color:var(--fz-normal-destaque); }}
.resumo.sev-aviso   {{ border-left-color:var(--fz-aviso-destaque); }}
.resumo.sev-critico {{ border-left-color:var(--fz-critico-destaque); }}
header {{ display:flex; justify-content:space-between; align-items:center; }}
h3 {{ margin:0; font-size:1.25rem; }}
p {{ margin:0; }}
.explicacao {{ font-size:1.0625rem; line-height:1.45; }}
.meta {{ color:var(--fz-texto-suave); font-size:0.875rem; }}
.status {{ align-self:flex-start; font-size:0.8125rem; padding:2px 10px; border-radius:{RAIO['pilula']}px;
          color:var(--fz-neutro-texto); background:var(--fz-neutro-fundo); }}
""",
    preparar=_com_severidade,
    para_markdown=lambda d: (
        f"### {_md(d['tag'])} · {d.get('simbolo', '')} {d.get('rotulo', '')}\n\n"
        f"{_md(d['explicacao'])}\n\n"
        f"{_md(d['titulo'])} · {_md(d['local'])} · leitura das {d['hora']} · "
        f"status operacional: {_md(d['status_operacional'])}"
    ),
)

# ---------------------------------------------------------------------------
# GRANDEZAS — grade fluida de cards com tendência em miniatura
# ---------------------------------------------------------------------------
GRANDEZAS = Componente(
    template="""
{{#if value}}
<div class="grade">
  {{#each value.itens}}
  <article class="card" aria-label="{{this.nome}}: {{this.valor}}">
    {{#if this.severidade}}
      <span class="selo sev-{{this.severidade}}"><span aria-hidden="true">{{this.simbolo}}</span>{{this.rotulo}}</span>
    {{else}}
      <span class="sem">Sem limite definido</span>
    {{/if}}
    <div class="nome">{{this.nome}}</div>
    <div class="valor">{{this.valor}}</div>
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true"><polyline points="{{this.pontos}}"/></svg>
  </article>
  {{/each}}
</div>
{{/if}}""",
    css=_CSS_SELO + f"""
/* Largura mínima + quebra automática: 2 por linha no celular, 4 ou 5 no monitor */
.grade {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(132px, 1fr)); gap:{ESPACO['sm']}px; }}
.card {{ border:1px solid var(--fz-borda); border-radius:{RAIO['md']}px; padding:{ESPACO['md']}px;
        display:flex; flex-direction:column; gap:{ESPACO['xs']}px; }}
.selo {{ align-self:flex-start; }}
.sem {{ color:var(--fz-texto-suave); font-size:0.8125rem; }}
.nome {{ color:var(--fz-texto-suave); font-size:0.9375rem; margin-top:{ESPACO['xs']}px; }}
.valor {{ font-size:1.375rem; font-weight:600; font-variant-numeric:tabular-nums; }}
svg {{ width:100%; height:28px; }}
polyline {{ fill:none; stroke:var(--fz-texto-suave); stroke-width:1.5; vector-effect:non-scaling-stroke; }}
""",
    preparar=lambda itens: {"itens": [{**_com_severidade(i), "pontos": _sparkline(i["serie"])} for i in itens]},
    para_markdown=lambda d: "\n".join(
        f"- **{i.get('simbolo', '')} {i.get('rotulo', '')} · {_md(i['nome'])}:** {i['valor']}"
        if i.get("severidade") else f"- **{_md(i['nome'])}:** {i['valor']}"
        for i in d["itens"]
    ),
)

# ---------------------------------------------------------------------------
# PARES — rótulo/valor (ficha, placa); substitui tabelas e arte ASCII
# ---------------------------------------------------------------------------
_CSS_PARES = f"""
h4 {{ margin:{ESPACO['lg']}px 0 {ESPACO['xs']}px; font-size:1rem; }}
dl {{ margin:0; }}
dl div {{ display:flex; justify-content:space-between; gap:{ESPACO['md']}px;
         padding:{ESPACO['sm']}px 0; border-bottom:1px solid var(--fz-borda-suave); }}
dt {{ color:var(--fz-texto-suave); }}
dd {{ margin:0; font-weight:600; text-align:right; }}
"""

PARES = Componente(
    template="""
{{#if value}}
  {{#each value.secoes}}
    {{#if this.titulo}}<h4>{{this.titulo}}</h4>{{/if}}
    <dl>{{#each this.pares}}<div><dt>{{this.r}}</dt><dd>{{this.v}}</dd></div>{{/each}}</dl>
  {{/each}}
{{/if}}""",
    css=_CSS_PARES,
    # aceita uma lista de pares (placa) ou a ficha completa com seções
    preparar=lambda d: {"secoes": [
        {"titulo": t, "pares": [{"r": r, "v": v} for r, v in ps]}
        for t, ps in (d["secoes"] if isinstance(d, dict) else [("", d)])
    ]},
    para_markdown=lambda d: "\n\n".join(
        (f"**{_md(s['titulo'])}**\n\n" if s["titulo"] else "")
        + "  \n".join(f"{_md(p['r'])}: **{_md(p['v'])}**" for p in s["pares"])
        for s in d["secoes"]
    ),
)

# ---------------------------------------------------------------------------
# CABEÇALHO DO CARD DE EQUIPAMENTO (os botões do card são gr.Button nativos)
# ---------------------------------------------------------------------------
EQUIPAMENTO = Componente(
    template="""
{{#if value}}
<div class="topo"><strong>{{value.tag}}</strong><span class="status">{{value.status}}</span></div>
<div class="titulo">{{value.titulo}}</div>
<div class="meta">{{value.detalhe}}<br>{{value.local}}</div>
{{/if}}""",
    css=f"""
.topo {{ display:flex; justify-content:space-between; align-items:center; }}
.topo strong {{ font-size:1.0625rem; }}
.status {{ font-size:0.8125rem; padding:2px 10px; border-radius:{RAIO['pilula']}px;
          color:var(--fz-neutro-texto); background:var(--fz-neutro-fundo); }}
.titulo {{ margin-top:{ESPACO['xs']}px; }}
.meta {{ color:var(--fz-texto-suave); font-size:0.875rem; margin-top:{ESPACO['xs']}px; }}
""",
    para_markdown=lambda d: (
        f"**{_md(d['tag'])}** · {_md(d['status'])}  \n{_md(d['titulo'])}  \n"
        f"{_md(d['detalhe'])} · {_md(d['local'])}"
    ),
)
