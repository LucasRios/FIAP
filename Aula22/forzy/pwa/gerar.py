# =============================================================================
# pwa/gerar.py — Gera os arquivos do PWA do Forzy
#
# Um PWA precisa, além do app, de:
#   - um MANIFESTO (nome, ícones, cores, modo de exibição, endereço inicial);
#   - ÍCONES em tamanhos e formatos específicos;
#   - um SERVICE WORKER (o script que fica entre a página e a rede);
#   - uma PÁGINA OFFLINE, para o service worker ter o que mostrar sem rede.
#
# Nada disso é escrito à mão. As cores vêm de ui/tokens.py (o design system
# do Forzy), como o tema do Streamlit e do Gradio. Trocar uma cor nos tokens
# e rodar este script atualiza também o app instalado no celular.
#
# Cada forma de publicar o Forzy tem um PERFIL:
#
#   python -m pwa.gerar gradio      → pwa/publico/  (servido pelo servidor.py)
#   python -m pwa.gerar streamlit   → static/       (servido pelo Streamlit)
#   python -m pwa.gerar casca URL   → docs/         (página no GitHub Pages que
#                                                    embrulha o app do
#                                                    Streamlit Community Cloud)
#
# Este arquivo é IDÊNTICO nas versões Streamlit e Gradio do Forzy.
# =============================================================================

import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# -----------------------------------------------------------------------------
# Cores: dos tokens do design system, quando existem
# -----------------------------------------------------------------------------
try:
    from ui.tokens import cores
except ImportError:
    # Forzy sem o design system mobile: a mesma paleta, escrita aqui.
    _PALETA = {
        "claro": {"fundo": "#FFFFFF", "texto": "#111827", "texto_suave": "#4B5563", "acao": "#1E40AF",
                  "texto_sobre_acao": "#FFFFFF", "borda": "#7D8794", "aviso_fundo": "#FFFBEB", "aviso_texto": "#92400E"},
        "escuro": {"fundo": "#0E1117", "texto": "#F3F4F6", "texto_suave": "#9CA3AF", "acao": "#2563EB",
                   "texto_sobre_acao": "#FFFFFF", "borda": "#7D8794", "aviso_fundo": "#451A03", "aviso_texto": "#FCD34D"},
    }

    def cores(modo: str = "claro") -> dict:
        return _PALETA["escuro" if modo in ("escuro", "dark") else "claro"]

NOME = "Forzy · Digital Twin"
NOME_CURTO = "Forzy"          # aparece embaixo do ícone: até ~12 caracteres
DESCRICAO = "Monitoramento de motores industriais: severidade, grandezas e ocorrências."

# Os nomes das páginas no deep link diferem entre as versões do Forzy, por
# isso cada perfil traz os próprios atalhos.
PERFIS = {
    "gradio": {
        "destino": "pwa/publico",
        "inicio": "/",                  # start_url e scope, como o NAVEGADOR os vê
        "service_worker": True,
        "atalhos": {"Painel": "?pagina=painel", "Sensores": "?pagina=sensores"},
    },
    "streamlit": {
        "destino": "static",            # o Streamlit serve esta pasta em /app/static/
        "inicio": "/",
        "service_worker": False,        # servido de /app/static/, não alcançaria a página
        "atalhos": {"Painel": "?pagina=dashboard", "Sensores": "?pagina=dados"},
    },
    "casca": {
        "destino": "docs",              # o GitHub Pages publica a pasta docs/ do repositório
        "inicio": "./",                 # relativo: funciona em qualquer subpasta
        "service_worker": True,
        "atalhos": {"Painel": "?pagina=dashboard", "Sensores": "?pagina=dados"},
    },
}

ICONES = {                              # arquivo -> (tamanho em px, formato)
    "icone-192.png": (192, "arredondado"),
    "icone-512.png": (512, "arredondado"),
    "icone-maskable-512.png": (512, "maskable"),
    "apple-touch-icon.png": (180, "cheio"),   # o iOS arredonda sozinho
    "favicon-32.png": (32, "arredondado"),
}


# -----------------------------------------------------------------------------
# 1. Ícones
# -----------------------------------------------------------------------------
def _engrenagem(desenho: ImageDraw.ImageDraw, cx: float, cy: float, raio: float, cor: str, fundo: str) -> None:
    """Engrenagem de 8 dentes desenhada com polígonos: nenhuma fonte ou imagem externa."""
    dentes, r_ext, r_int = 8, raio, raio * 0.76
    passo = math.pi * 2 / dentes
    pontos = []
    for i in range(dentes):
        base = i * passo
        # perfil de um dente: sobe, topo, desce, vale (frações do passo angular)
        for fracao, r in ((0.00, r_int), (0.12, r_ext), (0.38, r_ext), (0.50, r_int)):
            angulo = base + fracao * passo
            pontos.append((cx + r * math.cos(angulo), cy + r * math.sin(angulo)))
    desenho.polygon(pontos, fill=cor)
    furo = raio * 0.34
    desenho.ellipse((cx - furo, cy - furo, cx + furo, cy + furo), fill=fundo)


def _icone(tamanho: int, formato: str, cor_fundo: str, cor_simbolo: str) -> Image.Image:
    """
    Ícone em três formatos:
      arredondado  cantos transparentes, exibido como está (desktop, lista de apps);
      maskable     fundo até a borda, símbolo dentro do círculo central de 80%:
                   o Android recorta em círculo, gota ou quadrado;
      cheio        fundo até a borda, símbolo grande (o iOS arredonda sozinho).
    """
    escala = 4                                   # desenha 4x maior e reduz: bordas suaves
    t = tamanho * escala
    img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if formato == "arredondado":
        d.rounded_rectangle((0, 0, t - 1, t - 1), radius=t * 0.22, fill=cor_fundo)
        raio = t * 0.34
    else:
        d.rectangle((0, 0, t, t), fill=cor_fundo)
        raio = t * (0.26 if formato == "maskable" else 0.32)
    _engrenagem(d, t / 2, t / 2, raio, cor_simbolo, cor_fundo)
    return img.resize((tamanho, tamanho), Image.LANCZOS)


# -----------------------------------------------------------------------------
# 2. Manifesto
# -----------------------------------------------------------------------------
def manifesto(perfil: dict) -> dict:
    """
    Web App Manifest. O Chrome exige para instalar: name ou short_name,
    ícones de 192 e 512 px, start_url e display. O resto melhora a
    experiência: cores da tela de abertura, atalhos, id estável.
    """
    claro = cores("claro")
    inicio = perfil["inicio"]
    return {
        "id": inicio,                       # identidade do app instalado: não mude depois de publicar
        "name": NOME,
        "short_name": NOME_CURTO,
        "description": DESCRICAO,
        "lang": "pt-BR",
        "start_url": inicio,
        "scope": inicio,
        "display": "standalone",            # janela própria, sem barra de endereço
        "orientation": "portrait",
        "background_color": claro["fundo"], # tela de abertura enquanto o app carrega
        "theme_color": claro["fundo"],      # barra do sistema; o modo escuro vem do <meta>
        "icons": [
            {"src": "icones/icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icones/icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icones/icone-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        # Atalhos: toque longo no ícone instalado abre direto a tela. A URL
        # parte do start_url: "?pagina=..." sozinho seria resolvido a partir
        # do endereço do MANIFESTO (/manifest.json?pagina=...).
        "shortcuts": [
            {"name": nome, "url": inicio + consulta, "icons": [{"src": "icones/icone-192.png", "sizes": "192x192"}]}
            for nome, consulta in perfil["atalhos"].items()
        ],
    }


# -----------------------------------------------------------------------------
# 3. Página offline
# -----------------------------------------------------------------------------
def pagina_offline() -> str:
    """Página exibida quando não há rede. Autocontida: nenhum arquivo externo além do ícone em cache."""
    c, e = cores("claro"), cores("escuro")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Forzy · sem conexão</title>
<style>
  :root {{ color-scheme: light dark; --fundo:{c['fundo']}; --texto:{c['texto']}; --suave:{c['texto_suave']};
          --acao:{c['acao']}; --sobre:{c['texto_sobre_acao']}; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fundo:{e['fundo']}; --texto:{e['texto']}; --suave:{e['texto_suave']};
            --acao:{e['acao']}; --sobre:{e['texto_sobre_acao']}; }}
  }}
  body {{ margin:0; min-height:100dvh; display:grid; place-items:center; background:var(--fundo);
         color:var(--texto); font:16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width:22rem; padding:24px; text-align:center; }}
  img {{ width:72px; height:72px; }}
  h1 {{ font-size:1.25rem; margin:16px 0 8px; }}
  p {{ color:var(--suave); margin:0 0 24px; }}
  button {{ min-height:48px; padding:12px 24px; border:0; border-radius:8px; font:inherit; font-weight:600;
           background:var(--acao); color:var(--sobre); }}
</style>
</head>
<body>
<main>
  <img src="icones/icone-192.png" alt="">
  <h1>Sem conexão</h1>
  <p>O Forzy mostra leituras em tempo real e precisa da rede para isso.
     Nenhum dado antigo é exibido como se fosse atual.</p>
  <button onclick="location.reload()">Tentar de novo</button>
</main>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# 4. Service worker
# -----------------------------------------------------------------------------
def service_worker(versao: str, arquivos: list[str]) -> str:
    """
    Service worker para um app de dados em tempo real:
      - NAVEGAÇÃO: rede primeiro; sem rede, a página offline;
      - ARQUIVOS DO PWA (ícones, página offline): do cache;
      - TODO O RESTO (API, fila do Gradio, websocket do Streamlit): não toca.
    """
    return f"""// Gerado por `python -m pwa.gerar` — não edite à mão.
const CACHE = "forzy-{versao}";
const ARQUIVOS = {json.dumps(arquivos)};

self.addEventListener("install", (evento) => {{
  evento.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ARQUIVOS)));
  self.skipWaiting();                       // a versão nova assume sem esperar fechar todas as abas
}});

self.addEventListener("activate", (evento) => {{
  evento.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", (evento) => {{
  const pedido = evento.request;
  if (pedido.method !== "GET") return;

  if (pedido.mode === "navigate") {{
    evento.respondWith(fetch(pedido).catch(() => caches.match("offline.html")));
    return;
  }}

  const url = new URL(pedido.url);
  const escopo = new URL(self.registration.scope);
  const caminho = url.pathname.slice(escopo.pathname.length);
  if (url.origin === escopo.origin && ARQUIVOS.includes(caminho)) {{
    evento.respondWith(caches.match(pedido).then((r) => r || fetch(pedido)));
  }}
  // Qualquer outro pedido segue direto para a rede.
}});
"""


# -----------------------------------------------------------------------------
# 5. Script que liga a página ao PWA (Gradio e Streamlit)
# -----------------------------------------------------------------------------
def cabecalho_html(prefixo: str, registrar_sw: bool, link_manifesto: str | None = None) -> str:
    """
    Script que escreve no <head> o link do manifesto (quando o framework não
    escreve um), o ícone e o título do iOS, a cor da barra acompanhando o modo
    claro/escuro, e registra o service worker.

    É um SCRIPT, e não marcas prontas, porque nos dois frameworks esse
    conteúdo chega DEPOIS de a página carregar: o Gradio injeta o `head=` pelo
    JavaScript dele, e o st.html do Streamlit escreve no <body>, onde um
    <link rel="manifest"> seria ignorado.
    """
    c, e = cores("claro"), cores("escuro")
    manifesto_js = (f"garantir('link[rel=manifest]', () => criar('link', "
                    f"{{rel: 'manifest', href: '{link_manifesto}'}}));") if link_manifesto else ""
    registro_js = (f"if ('serviceWorker' in navigator) navigator.serviceWorker.register('{prefixo}sw.js');"
                   if registrar_sw else "")
    return f"""<script>
(() => {{
  const criar = (tag, atributos) => Object.assign(document.createElement(tag), atributos);
  const garantir = (seletor, fabrica) => document.head.querySelector(seletor) || document.head.appendChild(fabrica());
  {manifesto_js}
  garantir('link[rel=apple-touch-icon]', () => criar('link', {{rel: 'apple-touch-icon', href: '{prefixo}icones/apple-touch-icon.png'}}));
  garantir('meta[name=apple-mobile-web-app-title]', () => criar('meta', {{name: 'apple-mobile-web-app-title', content: '{NOME_CURTO}'}}));
  const cor = garantir('meta[name=theme-color]', () => criar('meta', {{name: 'theme-color'}}));
  const escuro = matchMedia('(prefers-color-scheme: dark)');
  const pintar = () => {{ cor.content = escuro.matches ? '{e['fundo']}' : '{c['fundo']}'; }};
  pintar();
  escuro.addEventListener('change', pintar);
  {registro_js}
}})();
</script>"""


# -----------------------------------------------------------------------------
# 6. Casca para o Streamlit Community Cloud
# -----------------------------------------------------------------------------
def pagina_casca(url_app: str) -> str:
    """
    No Streamlit Community Cloud, a página principal pertence à plataforma
    (com o manifesto dela). A casca inverte isso: uma página NOSSA, no GitHub
    Pages, carrega o app num iframe pelo modo de incorporação oficial do
    Streamlit (?embed=true) e repassa os parâmetros da URL (deep links).
    """
    c, e = cores("claro"), cores("escuro")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{NOME}</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icones/favicon-32.png">
<link rel="apple-touch-icon" href="icones/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="{NOME_CURTO}">
<meta name="theme-color" content="{c['fundo']}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{e['fundo']}" media="(prefers-color-scheme: dark)">
<style>
  :root {{ --fundo:{c['fundo']}; --aviso-fundo:{c['aviso_fundo']}; --aviso-texto:{c['aviso_texto']}; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fundo:{e['fundo']}; --aviso-fundo:{e['aviso_fundo']}; --aviso-texto:{e['aviso_texto']}; }}
  }}
  html, body {{ margin:0; height:100%; background:var(--fundo);
               font:16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  /* viewport-fit=cover + safe-area: nada sob o entalhe nem sob a barra de gestos */
  body {{ box-sizing:border-box; padding:env(safe-area-inset-top) env(safe-area-inset-right)
                                       env(safe-area-inset-bottom) env(safe-area-inset-left); }}
  iframe {{ display:block; width:100%; height:100%; border:0; }}
  #sem-rede {{ position:fixed; left:12px; right:12px; top:calc(12px + env(safe-area-inset-top));
              padding:12px 16px; border-radius:12px; font-weight:600;
              background:var(--aviso-fundo); color:var(--aviso-texto); box-shadow:0 4px 16px rgba(0,0,0,.2); }}
</style>
</head>
<body>
<iframe id="app" title="{NOME}" allow="clipboard-write"></iframe>
<div id="sem-rede" role="status" hidden>▲ Sem conexão. As leituras na tela podem estar desatualizadas.</div>
<script>
  const APP = {json.dumps(url_app)};
  const destino = new URL(APP);
  new URLSearchParams(location.search).forEach((valor, chave) => destino.searchParams.set(chave, valor));
  destino.searchParams.set("embed", "true");
  document.getElementById("app").src = destino.href;

  // Sem rede, o app dentro do iframe congela em silêncio. A casca avisa.
  const aviso = document.getElementById("sem-rede");
  const atualizar = () => {{ aviso.hidden = navigator.onLine; }};
  addEventListener("online", atualizar);
  addEventListener("offline", atualizar);
  atualizar();

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# 7. Geração
# -----------------------------------------------------------------------------
def gerar(nome_perfil: str, raiz: Path = Path("."), url_app: str | None = None) -> Path:
    """Escreve manifesto, ícones e, se o perfil pede, service worker e página offline."""
    perfil = PERFIS[nome_perfil]
    if nome_perfil == "casca" and not (url_app or "").startswith(("https://", "http://localhost")):
        raise ValueError("A casca precisa do endereço HTTPS do app, ex.: https://forzy.streamlit.app")

    destino = raiz / perfil["destino"]
    (destino / "icones").mkdir(parents=True, exist_ok=True)

    claro = cores("claro")
    for arquivo, (tamanho, formato) in ICONES.items():
        _icone(tamanho, formato, claro["acao"], claro["texto_sobre_acao"]).save(destino / "icones" / arquivo)

    (destino / "manifest.webmanifest").write_text(
        json.dumps(manifesto(perfil), ensure_ascii=False, indent=2), encoding="utf-8")

    if perfil["service_worker"]:
        # Sem service worker, ninguém serviria a página offline: ela só existe junto com ele.
        (destino / "offline.html").write_text(pagina_offline(), encoding="utf-8")
        arquivos = ["offline.html", *[f"icones/{a}" for a in ICONES]]
        # A versão do cache é a impressão digital dos arquivos guardados: mudou
        # um ícone ou a página offline, muda o sw.js, e o navegador instala a
        # versão nova sozinho.
        impressao = hashlib.sha256()
        for a in sorted(arquivos):
            impressao.update((destino / a).read_bytes())
        (destino / "sw.js").write_text(service_worker(impressao.hexdigest()[:10], arquivos), encoding="utf-8")

    if nome_perfil == "casca":
        (destino / "index.html").write_text(pagina_casca(url_app), encoding="utf-8")

    return destino


if __name__ == "__main__":
    perfil = sys.argv[1] if len(sys.argv) > 1 else ""
    if perfil not in PERFIS:
        sys.exit("Uso: python -m pwa.gerar gradio | streamlit | casca https://SEU-APP.streamlit.app")
    try:
        print(f"Arquivos do PWA gerados em {gerar(perfil, url_app=sys.argv[2] if len(sys.argv) > 2 else None)}/")
    except ValueError as erro:
        sys.exit(str(erro))
