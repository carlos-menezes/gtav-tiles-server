#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "Pillow",
# ]
# ///
"""
GTA V map tile generator
------------------------
Usage:
  uv run main.py <input_image> [--zoom 0-8] [--tile-size 256] [--out ./tiles]

Example:
  uv run main.py gta_map.png
  uv run main.py gta_map.png --zoom 0-6 --out ./my_tiles

Outputs:
  tiles/{z}/{x}/{y}.png — XYZ tile tree
"""

import argparse
import math
import sys
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# ── Mercator helpers ──────────────────────────────────────────────────────────

def tile_to_lng(x: int, z: int) -> float:
    return x / 2**z * 360 - 180

def tile_to_lat(y: int, z: int) -> float:
    n = math.pi - 2 * math.pi * y / 2**z
    return math.degrees(math.atan(math.sinh(n)))

# ── Tile generation ───────────────────────────────────────────────────────────

def generate_tiles(
    img: Image.Image,
    out_dir: Path,
    min_zoom: int,
    max_zoom: int,
    tile_size: int,
) -> tuple[int, int]:
    """
    Slice img into XYZ tiles. At each zoom level the image is resized to
    (num_tiles * tile_size) then cut into a grid.

    Returns (num_tiles_x, num_tiles_y) at max_zoom.
    """
    img_w, img_h = img.size
    # Keep aspect ratio — fit into a square tile grid at max zoom
    num_tiles_max = 2 ** max_zoom
    canvas_size = num_tiles_max * tile_size

    # Scale image to fit canvas, letterboxing the shorter axis
    scale = min(canvas_size / img_w, canvas_size / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    # How many tiles does the image actually fill at max_zoom?
    tiles_x = math.ceil(new_w / tile_size)
    tiles_y = math.ceil(new_h / tile_size)

    total = sum((2**z) * (2**z) for z in range(min_zoom, max_zoom + 1))
    done = 0

    for z in range(min_zoom, max_zoom + 1):
        num_tiles = 2 ** z
        size = num_tiles * tile_size

        # Scale image to this zoom level
        zscale = min(size / img_w, size / img_h)
        zw = int(img_w * zscale)
        zh = int(img_h * zscale)
        resized = img.resize((zw, zh), Image.LANCZOS)

        # Paste onto a black canvas of full tile-grid size
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(resized, (0, 0))

        tiles_x_z = math.ceil(zw / tile_size)
        tiles_y_z = math.ceil(zh / tile_size)

        for x in range(tiles_x_z):
            for y in range(tiles_y_z):
                left   = x * tile_size
                upper  = y * tile_size
                right  = left + tile_size
                lower  = upper + tile_size
                tile   = canvas.crop((left, upper, right, lower))

                tile_path = out_dir / str(z) / str(x)
                tile_path.mkdir(parents=True, exist_ok=True)
                tile.convert("RGB").save(tile_path / f"{y}.png", "PNG", optimize=True)

                done += 1

        pct = done / total * 100
        print(f"  zoom {z}: {tiles_x_z}×{tiles_y_z} tiles  ({pct:.0f}%)", flush=True)

    return tiles_x, tiles_y


def compute_bounds(tiles_x: int, tiles_y: int, max_zoom: int):
    """
    Convert tile grid dimensions to lng/lat bounds.
    """
    w = tile_to_lng(0,       max_zoom)
    e = tile_to_lng(tiles_x, max_zoom)
    n = tile_to_lat(0,       max_zoom)
    s = tile_to_lat(tiles_y, max_zoom)
    center_lng = (w + e) / 2
    center_lat = (n + s) / 2
    return w, s, e, n, center_lng, center_lat


def print_tile_info(w, s, e, n, cx, cy, max_zoom, tile_size):
    print("\n" + "─" * 60)
    print("Bounds (W, S, E, N) :" , f"{w:.6f}, {s:.6f}, {e:.6f}, {n:.6f}")
    print("Center (lng, lat)   :", f"{cx:.6f}, {cy:.6f}")
    print("Zoom range          :", f"0 – {max_zoom}")
    print("Tile size           :", f"{tile_size}px")
    print("─" * 60 + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_zoom(zoom_str: str) -> tuple[int, int]:
    if "-" in zoom_str:
        parts = zoom_str.split("-")
        return int(parts[0]), int(parts[1])
    z = int(zoom_str)
    return 0, z


def main():
    parser = argparse.ArgumentParser(description="Slice a map image into XYZ tiles.")
    parser.add_argument("image",      help="Path to your map image (PNG, JPG, WEBP, etc.)")
    parser.add_argument("--zoom",     default="0-8", help="Zoom range, e.g. 0-8 (default: 0-8)")
    parser.add_argument("--tile-size",default=256, type=int, help="Tile size in pixels (default: 256)")
    parser.add_argument("--out",      default="./tiles", help="Output directory (default: ./tiles)")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"❌  File not found: {img_path}")
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    min_zoom, max_zoom = parse_zoom(args.zoom)
    tile_size = args.tile_size

    print(f"📂  Input : {img_path}")
    print(f"📁  Output: {out_dir}")
    print(f"🔍  Zoom  : {min_zoom}–{max_zoom}  |  Tile size: {tile_size}px\n")

    img = Image.open(img_path).convert("RGBA")
    print(f"🖼️   Image size: {img.width}×{img.height}px\n")
    print("⚙️   Generating tiles...")

    tiles_x, tiles_y = generate_tiles(img, out_dir, min_zoom, max_zoom, tile_size)
    w, s, e, n, cx, cy = compute_bounds(tiles_x, tiles_y, max_zoom)
    print_tile_info(w, s, e, n, cx, cy, max_zoom, tile_size)


if __name__ == "__main__":
    main()
