"""
Testes de fluxo do Forzy Gradio num navegador real (Playwright), em tela de celular.

Pré-requisitos: a API respondendo e o app rodando em URL_APP (padrão http://localhost:7860).
Rode:  python -m testes.teste_fluxos
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

URL = os.getenv("URL_APP", "http://localhost:7860").rstrip("/")
falhas = 0


def checar(rotulo: str, ok: bool, detalhe: str = "") -> None:
    global falhas
    falhas += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'}  {rotulo} {detalhe}")


async def main():
    async with async_playwright() as p:
        nav = await p.chromium.launch()
        ctx = await nav.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))

        # 1. Card da lista -> painel do motor, com URL atualizada
        await pg.goto(URL + "/"); await pg.wait_for_timeout(6000)
        cards = await pg.locator(".fz-card").get_by_role("button", name="Ficha").count()
        checar("lista mostra um card por motor", cards >= 20, f"({cards})")
        card = pg.locator(".fz-card", has_text="MTR-007").last
        await card.get_by_role("button", name="Painel").click(); await pg.wait_for_timeout(4000)
        aba = await pg.evaluate("[...document.querySelectorAll('#nav [role=tab]')]"
                                ".filter(t => t.getAttribute('aria-selected') === 'true').map(t => t.innerText)[0]")
        resumo = aba == "Painel" and await pg.locator("text=MTR-007 >> visible=true").count() > 0
        checar("card MTR-007 -> painel", resumo and "pagina=painel" in pg.url and "tag=MTR-007" in pg.url, pg.url.split("/")[-1])

        # 2. Deep link para a ficha
        await pg.goto(URL + "/?pagina=cadastro&tag=MTR-012"); await pg.wait_for_timeout(6000)
        checar("deep link -> ficha do MTR-012", await pg.get_by_text("Motor MTR-012").is_visible())

        # 3. Deep link com valores inválidos cai na lista
        await pg.goto(URL + "/?pagina=<script>&tag=../../etc"); await pg.wait_for_timeout(6000)
        checar("deep link inválido -> lista", await pg.locator(".fz-card").get_by_role("button", name="Ficha").count() >= 20)

        # 4. Cadastro: TAG inválida é recusada antes de chamar a API
        await pg.goto(URL + "/?pagina=cadastro"); await pg.wait_for_timeout(6000)
        await pg.get_by_label("TAG").fill("motor 7")
        await pg.get_by_label("Modelo").fill("W22 Teste Gradio")
        await pg.get_by_role("button", name="Salvar").click(); await pg.wait_for_timeout(2500)
        checar("TAG inválida mostra aviso", await pg.get_by_text("Use o formato MTR-000").first.is_visible())

        # 5. Cadastro válido grava e abre a ficha do novo motor
        await pg.get_by_label("TAG").fill("MTR-098")
        await pg.get_by_role("button", name="Salvar").click(); await pg.wait_for_timeout(4000)
        checar("cadastro grava e abre a ficha", await pg.get_by_text("Motor MTR-098").is_visible())

        # 6. Alvos de toque (nível avançado): botões de ação e abas com >= 48 px
        await pg.goto(URL + "/?pagina=painel&tag=MTR-007"); await pg.wait_for_timeout(6000)
        alturas = await pg.evaluate("""() => [...document.querySelectorAll('.fz-acoes button, #nav [role=tab]')]
            .filter(b => b.offsetParent).map(b => Math.round(b.getBoundingClientRect().height))""")
        checar("alvos de toque >= 48 px", bool(alturas) and min(alturas) >= 48, str(sorted(set(alturas))))

        checar("sem erros de JavaScript", not erros, "; ".join(erros[:2]))
        await nav.close()

    print(f"\n{'Tudo certo.' if not falhas else f'{falhas} falha(s).'}")
    sys.exit(1 if falhas else 0)


asyncio.run(main())
