# =============================================================================
# servidor.py — O Forzy (Gradio) como PWA instalável
#
# O Gradio roda sobre FastAPI. Em vez de app.launch(), montamos a interface
# DENTRO de uma aplicação FastAPI nossa — a mesma ferramenta da API do Forzy.
# Assim ganhamos o controle das rotas que um PWA precisa na RAIZ do site:
#
#   /manifest.json   o manifesto (o HTML do Gradio já aponta para este
#                    endereço; nossa rota responde antes da dele)
#   /sw.js           o service worker — na raiz, para controlar o app inteiro
#   /offline.html    a página exibida sem rede
#   /icones/...      os ícones
#
# Os arquivos vêm de pwa/publico/, gerados por `python -m pwa.gerar gradio`.
#
# Local:   uvicorn servidor:servidor --port 7860
# Render:  uvicorn servidor:servidor --host 0.0.0.0 --port $PORT
# =============================================================================

from pathlib import Path

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import app as interface          # o gr.Blocks do app.py, sem nenhuma mudança
from pwa.gerar import cabecalho_html

# Tema e CSS do design system mobile, quando o projeto tem essa camada.
try:
    from ui.tema import CSS_GLOBAL, criar_tema
    TEMA, CSS = criar_tema(), CSS_GLOBAL
except ImportError:
    TEMA, CSS = None, None

PUBLICO = Path(__file__).parent / "pwa" / "publico"
if not (PUBLICO / "manifest.webmanifest").exists():
    raise SystemExit("Arquivos do PWA não encontrados. Rode antes: python -m pwa.gerar gradio")

servidor = FastAPI(title="Forzy · front-end", docs_url=None, redoc_url=None, openapi_url=None)


# As rotas abaixo são registradas ANTES de montar o Gradio: numa aplicação
# FastAPI, a primeira rota que casa com o endereço é a que responde.
@servidor.get("/manifest.json", include_in_schema=False)
def manifesto() -> FileResponse:
    return FileResponse(PUBLICO / "manifest.webmanifest", media_type="application/manifest+json")


@servidor.get("/sw.js", include_in_schema=False)
def service_worker() -> FileResponse:
    # no-cache: o navegador sempre confere com o servidor se há versão nova.
    return FileResponse(PUBLICO / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache"})


@servidor.get("/offline.html", include_in_schema=False)
def pagina_offline() -> FileResponse:
    return FileResponse(PUBLICO / "offline.html", media_type="text/html")


servidor.mount("/icones", StaticFiles(directory=PUBLICO / "icones"), name="icones")

# O que no app.py ia no launch() (tema, CSS, cabeçalho) aqui vai na montagem.
servidor = gr.mount_gradio_app(
    servidor, interface, path="/",
    theme=TEMA,
    css=CSS,
    head=cabecalho_html(prefixo="/", registrar_sw=True),
    favicon_path=str(PUBLICO / "icones" / "icone-192.png"),
    footer_links=[],
)
