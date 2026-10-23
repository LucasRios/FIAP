"""Gera os ícones do PWA mínimo: um círculo branco sobre fundo azul (só Pillow, sem fontes)."""
from pathlib import Path

from PIL import Image, ImageDraw

AZUL, BRANCO = "#1E40AF", "#FFFFFF"
PASTA = Path(__file__).parent / "icones"
PASTA.mkdir(exist_ok=True)


def icone(tamanho: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if maskable:
        d.rectangle((0, 0, tamanho, tamanho), fill=AZUL)          # fundo até a borda
        r = tamanho * 0.22                                         # símbolo dentro da zona segura
    else:
        d.rounded_rectangle((0, 0, tamanho - 1, tamanho - 1), radius=tamanho * 0.22, fill=AZUL)
        r = tamanho * 0.30
    c = tamanho / 2
    d.ellipse((c - r, c - r, c + r, c + r), outline=BRANCO, width=max(2, int(tamanho * 0.06)))
    return img


icone(192, False).save(PASTA / "icone-192.png")
icone(512, False).save(PASTA / "icone-512.png")
icone(512, True).save(PASTA / "icone-maskable-512.png")
icone(180, True).save(PASTA / "apple-touch-icon.png")
print("ícones gerados em", PASTA)
