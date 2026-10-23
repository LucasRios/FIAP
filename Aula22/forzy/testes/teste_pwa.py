"""
Verifica se o app publicado é um PWA instalável, num Chrome de verdade.

O Lighthouse não tem mais a categoria PWA (removida na versão 12, em 2024),
e o método do DevTools que respondia "é instalável?" não é confiável em modo
automatizado. Então o teste confere, um a um, os critérios que o Chrome
publica (web.dev/articles/install-criteria):

  - página servida por HTTPS (localhost vale como seguro, para testes);
  - manifesto encontrado e lido sem erros pelo navegador;
  - name ou short_name;
  - ícones de 192 e 512 px que REALMENTE existem e têm esse tamanho;
  - start_url dentro do scope;
  - display standalone, fullscreen, minimal-ui ou window-controls-overlay;
  - prefer_related_applications ausente ou falso;

e, quando há service worker:

  - ele controla a página;
  - a página offline está guardada no cache.

Uso:  URL_APP=http://localhost:7860 python -m testes.teste_pwa
      ESPERA_SW=0 para apps sem service worker (Streamlit servindo a si mesmo)
"""
import asyncio
import io
import os
import sys
import tempfile
from urllib.parse import urljoin, urlparse

from PIL import Image
from playwright.async_api import async_playwright

URL = os.getenv("URL_APP", "http://localhost:7860").rstrip("/") + "/"
ESPERA_SW = os.getenv("ESPERA_SW", "1") == "1"
DISPLAYS = {"standalone", "fullscreen", "minimal-ui", "window-controls-overlay"}
falhas = 0


def checar(rotulo: str, ok: bool, detalhe: str = "") -> None:
    global falhas
    falhas += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'}  {rotulo} {detalhe}")


def aviso(rotulo: str, ok: bool, detalhe: str = "") -> None:
    """Recomendações: não reprovam, mas aparecem."""
    print(f"{'ok   ' if ok else 'aviso'}  {rotulo} {detalhe}")


async def main():
    origem = urlparse(URL)
    checar("origem segura (HTTPS ou localhost)",
           origem.scheme == "https" or origem.hostname in ("localhost", "127.0.0.1"), origem.netloc)

    async with async_playwright() as p:
        # Contexto PERSISTENTE: numa janela anônima o Chrome nunca oferece instalação.
        with tempfile.TemporaryDirectory() as perfil:
            ctx = await p.chromium.launch_persistent_context(
                perfil, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await pg.goto(URL)
            await pg.wait_for_timeout(6000)

            # 1. O navegador encontrou e leu o manifesto?
            cdp = await ctx.new_cdp_session(pg)
            m = await cdp.send("Page.getAppManifest")
            url_manifesto = m.get("url", "")
            checar("manifesto encontrado", bool(url_manifesto), url_manifesto)
            erros = [e["message"] for e in m.get("errors", [])]
            checar("manifesto lido sem erros", bool(url_manifesto) and not erros, "; ".join(erros))
            if not url_manifesto or erros:
                await ctx.close()
                return

            man = await (await ctx.request.get(url_manifesto)).json()

            # 2. Os critérios do Chrome, campo a campo
            nome = man.get("short_name") or man.get("name")
            checar("name ou short_name", bool(nome) and nome not in ("Gradio", "Streamlit"), str(nome))
            aviso("short_name com até 12 caracteres", len(man.get("short_name", "")) in range(1, 13),
                  repr(man.get("short_name")))
            checar("display instalável", man.get("display") in DISPLAYS, str(man.get("display")))
            checar("prefer_related_applications falso", not man.get("prefer_related_applications"))

            inicio = urljoin(url_manifesto, man.get("start_url", ""))
            escopo = urljoin(url_manifesto, man.get("scope", "./"))
            checar("start_url dentro do scope", bool(man.get("start_url")) and inicio.startswith(escopo),
                   f"{inicio} em {escopo}")

            tamanhos = set()
            for icone in man.get("icons", []):
                r = await ctx.request.get(urljoin(url_manifesto, icone["src"]))
                if r.ok:
                    try:
                        largura, altura = Image.open(io.BytesIO(await r.body())).size
                        if f"{largura}x{altura}" in icone.get("sizes", "").split():
                            tamanhos.add(largura)
                    except Exception:
                        pass
            checar("ícones de 192 e 512 px existem", {192, 512} <= tamanhos, str(sorted(tamanhos)))
            aviso("ícone maskable", any("maskable" in i.get("purpose", "") for i in man.get("icons", [])))

            # 3. Service worker
            if ESPERA_SW:
                await pg.reload()
                await pg.wait_for_timeout(4000)
                checar("service worker controla a página", await pg.evaluate("!!navigator.serviceWorker.controller"))
                # A simulação de "offline" do Playwright não alcança o service worker no
                # Chromium; conferimos que a página offline está no cache. O teste real é
                # manual: DevTools → Application → Service workers → "Offline" → recarregar.
                em_cache = await pg.evaluate("""async () => {
                    for (const nome of await caches.keys()) {
                        const r = await (await caches.open(nome)).match('offline.html');
                        if (r) return (await r.text()).includes('Sem conexão');
                    }
                    return false; }""")
                checar("página offline guardada no cache", em_cache)

            await ctx.close()


asyncio.run(main())
print(f"\n{'Tudo certo.' if not falhas else f'{falhas} falha(s).'}")
sys.exit(1 if falhas else 0)
