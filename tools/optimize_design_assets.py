#!/usr/bin/env python3
"""Reduce los assets de public/assets/ al tamano en que realmente se muestran.

El HTML de diseno llega con las imagenes embebidas en base64 y a resolucion de
exportacion, muy por encima de su tamano en pantalla: icon-infografia.png venia
a 938x938 (879 KB) para mostrarse a 48 px. Este script las baja a 3x su tamano
CSS, que cubre pantallas retina de sobra.

Ejecucion puntual tras importar un diseno nuevo:
    python3 tools/optimize_design_assets.py
"""
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "public" / "assets"
SCALE = 3  # margen para pantallas de alta densidad

# Ancho CSS de cada asset, tomado de las reglas en public/index.html:
#   .r3d-section 80px · .r3d-inline 48px · .r3d-contact 90px
TARGET_WIDTH = {
    "icon-podcast.png": 48,
    "icon-infografia.png": 48,
    "icon-video.png": 48,
    "r3d-recursos.png": 48,
    "r3d-cursos.png": 80,
    "r3d-planes.png": 80,
    "r3d-contacto.png": 90,
}
# El logo se dimensiona por alto (.brand-mark{height:52px}), no por ancho.
TARGET_HEIGHT = {"logo-brand.png": 52}


def resize(path: Path, target: int, by_height: bool) -> None:
    im = Image.open(path)
    cur = im.height if by_height else im.width
    if cur <= target:
        print(f"  {path.name:28} {cur}px ya <= {target}px, se deja")
        return
    ratio = target / cur
    new = (max(1, round(im.width * ratio)), max(1, round(im.height * ratio)))
    before = path.stat().st_size
    im.resize(new, Image.LANCZOS).save(path, optimize=True)
    after = path.stat().st_size
    print(f"  {path.name:28} -> {new[0]}x{new[1]:<4} "
          f"{before/1024:8.1f} KB -> {after/1024:7.1f} KB")


def main() -> None:
    total_before = sum(f.stat().st_size for f in ASSETS.iterdir())
    for name, w in TARGET_WIDTH.items():
        resize(ASSETS / name, w * SCALE, by_height=False)
    for name, h in TARGET_HEIGHT.items():
        resize(ASSETS / name, h * SCALE, by_height=True)
    total_after = sum(f.stat().st_size for f in ASSETS.iterdir())
    print(f"\n  total public/assets: {total_before/1024/1024:.2f} MB -> "
          f"{total_after/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
