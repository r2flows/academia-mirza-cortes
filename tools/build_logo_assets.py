#!/usr/bin/env python3
"""Genera los assets web de marca a partir de brand/logo_mirza.jpeg.

Ejecucion puntual, no forma parte del build:
    python3 tools/build_logo_assets.py

El JPEG original es un tile blanco de 765x765 con esquinas squircle sobre un
fondo lavanda opaco. Como el sitio tiene header purpura oscuro, ese fondo hay
que convertirlo en transparencia. La mascara alfa no se dibuja a ojo: se deriva
del propio pixel data con un flood fill desde las cuatro esquinas, asi sigue la
curva squircle real en vez de aproximarla con un border-radius.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brand" / "logo_mirza.jpeg"
OUT = ROOT / "public"

# Medido sobre el original (pixeles blancos puros): el tile es un cuadrado exacto.
TILE = (158, 68, 923, 833)          # left, top, right, bottom -> 765x765
# Emblema (microscopio + elipse dorada) en coordenadas relativas al tile.
EMBLEM = (189, 83, 569, 351)        # 380x268

BRAND_TOP = (75, 46, 158)           # #4B2E9E
BRAND_BOTTOM = (58, 35, 128)        # #3A2380


def squircle_alpha(tile: Image.Image) -> Image.Image:
    """Alfa del tile: opaco en el logo, transparente en las esquinas lavanda.

    Dentro del recorte exacto al tile blanco, lo unico que no es logo son las
    cuatro esquinas de fondo. Se marcan con un flood fill desde las esquinas,
    pero restringido a pixeles "de fondo" -- lavanda o sombra: claros, muy
    desaturados y nunca blanco puro. Sin esa restriccion el fill se escapa al
    tile, porque el lavanda #F2EFF6 dista solo 38 del blanco.
    """
    from collections import deque

    a = np.asarray(tile.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    lo = a.min(axis=2)
    sat = a.max(axis=2) - lo
    # Fondo: no es blanco puro (<248), es claro (>195) y casi gris (sat<30).
    # La tinta del logo queda fuera por oscura (morado) o saturada (dorado).
    is_bg = (lo < 248) & (lo > 195) & (sat < 30)

    outside = np.zeros((h, w), dtype=bool)
    q = deque()
    for sy, sx in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if is_bg[sy, sx] and not outside[sy, sx]:
            outside[sy, sx] = True
            q.append((sy, sx))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and is_bg[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))

    alpha = Image.fromarray(np.where(outside, 0, 255).astype(np.uint8), "L")
    # Suaviza el borde dentado que deja el umbral duro sobre una curva.
    return alpha.filter(ImageFilter.GaussianBlur(0.6))


def rounded_mask(size: int, radius_ratio: float = 0.265) -> Image.Image:
    """Squircle sintetico para los lienzos que componemos desde cero."""
    ss = 4  # supersampling para un borde limpio
    m = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (0, 0, size * ss - 1, size * ss - 1),
        radius=int(size * ss * radius_ratio),
        fill=255,
    )
    return m.resize((size, size), Image.LANCZOS)


def vertical_gradient(size, top, bottom) -> Image.Image:
    w, h = size
    ramp = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    px = (np.array(top, np.float32) * (1 - ramp) + np.array(bottom, np.float32) * ramp)
    return Image.fromarray(
        np.repeat(px[:, None, :], w, axis=1).astype(np.uint8), "RGB"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tile = Image.open(SRC).convert("RGB").crop(TILE)

    # 1. Lockup completo con esquinas transparentes.
    full = tile.copy()
    full.putalpha(squircle_alpha(tile))
    full.save(ROOT / "brand" / "logo-full.png", optimize=True)

    # 2. Marca: solo el emblema, recentrado en un tile blanco squircle propio.
    #    El wordmark del lockup es ilegible a 36px y el sitio ya lo muestra
    #    como texto vivo, asi que a tamano pequeno solo va el emblema.
    S = 512
    emblem = tile.crop(EMBLEM)
    # Escala por el ancho: la elipse dorada es ancha y plana, asi que ajustar
    # por el lado mayor dejaria el microscopio diminuto a 36px.
    scale = (S * 0.86) / emblem.width
    emblem = emblem.resize(
        (round(emblem.width * scale), round(emblem.height * scale)), Image.LANCZOS
    )
    mark = Image.new("RGB", (S, S), (255, 255, 255))
    mark.paste(emblem, ((S - emblem.width) // 2, (S - emblem.height) // 2))
    mark_rgba = mark.convert("RGBA")
    mark_rgba.putalpha(rounded_mask(S))
    # Se compone a 512 por calidad, pero se publica a 192: en la pagina se
    # muestra a 36px y 28px, asi que 192 ya cubre pantallas 4x de sobra y
    # ahorra ~120 KB frente a servir el lienzo completo.
    mark_rgba.resize((192, 192), Image.LANCZOS).save(
        OUT / "logo-mark.png", optimize=True
    )

    # 3. apple-touch-icon: iOS ignora el alfa y pinta negro detras, asi que
    #    va opaco y con las esquinas que el propio iOS recorta.
    mark.resize((180, 180), Image.LANCZOS).save(
        OUT / "apple-touch-icon.png", optimize=True
    )

    # 4. Favicon multi-tamano.
    mark_rgba.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    # 5. Open Graph: el lockup completo sobre el degradado purpura de marca.
    og = vertical_gradient((1200, 630), BRAND_TOP, BRAND_BOTTOM)
    logo_h = 470
    logo = full.resize((logo_h, logo_h), Image.LANCZOS)
    og.paste(logo, ((1200 - logo_h) // 2, (630 - logo_h) // 2), logo)
    og.save(OUT / "og-image.jpg", quality=90, optimize=True, progressive=True)

    for f in sorted(OUT.iterdir()) + [ROOT / "brand" / "logo-full.png"]:
        if f.suffix in {".png", ".ico", ".jpg"}:
            print(f"  {f.relative_to(ROOT)!s:28} {f.stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
