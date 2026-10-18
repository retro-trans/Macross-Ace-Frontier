"""Paint the release version and group name into the bottom-right corner of the title screen.

Usage:
  python tools/title_tag.py --version <0.x.y> [--in <title.gim>] [--out <title.gim>]
                            [--author github.com/retro-trans] [--font <ttf>] [--preview <png>]

The title screen background is data/menu/title/title.gim: 480x272, 8-bit indices with a 256-colour
palette (the copyright lines at the bottom left are part of it and are redrawn by
tools/redraw_images.py). Two right-aligned lines, like the Super Robot Wars Z patch:

    v0.2.2
    github.com / retro-trans

white with a one-pixel dark outline, ending 6 px from the right edge, in the empty strip below the
"PRESS START BUTTON" plate. Only pixels inside the label box change. They are mapped to the nearest
colours already in the texture's palette, so the palette and every other pixel stay as they are.

--in defaults to the build overlay's title.gim when it exists (the redrawn copyright lines), else
the extracted original. Always paint a clean texture: tools/build_iso.py recreates the overlay on
every build, so the tag is never drawn twice.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim  # noqa: E402

TITLE = os.path.join("data", "menu", "title", "title.gim")
W, H = 480, 272
RIGHT = 474          # last column of the text
TOPS = (240, 254)    # first row of each line
SIZE = 11            # px
FONTS = [r"C:\Windows\Fonts\arialbd.ttf", os.path.join("work", "fonts", "GenEiLateGo_v2.ttc")]
INK, OUTLINE = (255, 255, 255, 255), (0, 0, 0, 255)


def label(draw_text, version, author, font):
    """RGBA layer (W x H) with the two right-aligned lines, outlined."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for text, top in ((version, TOPS[0]), (author, TOPS[1])):
        box = d.textbbox((0, 0), text, font=font, stroke_width=1)
        x = RIGHT - (box[2] - box[0]) - box[0]
        y = top - box[1]
        d.text((x, y), text, font=font, fill=INK, stroke_width=1, stroke_fill=OUTLINE)
    return layer


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True, help="e.g. 0.2.2 (a leading v is added)")
    ap.add_argument("--author", default="github.com / retro-trans")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", default=os.path.join("work", "output", "build", "overlay", TITLE))
    ap.add_argument("--font")
    ap.add_argument("--preview")
    a = ap.parse_args()
    src = a.src or (a.out if os.path.exists(a.out) else os.path.join("work", "source", "dat", TITLE))
    font_path = a.font or next(f for f in FONTS if os.path.exists(f))
    font = ImageFont.truetype(font_path, SIZE)
    version = a.version if a.version.startswith("v") else "v" + a.version

    data = open(src, "rb").read()
    fmt, w, h, idx, pal = gim.read_indexed(data)
    if (fmt, w, h) != (5, W, H):
        raise SystemExit("%s: expected an 8-bit %dx%d texture, got format %d %dx%d" % (src, W, H, fmt, w, h))
    pal_arr = np.array(pal, np.uint8)
    rgba = pal_arr[np.frombuffer(bytes(idx), np.uint8)].reshape(H, W, 4)

    layer = label(None, version, a.author, font)
    over = Image.alpha_composite(Image.fromarray(rgba, "RGBA"), layer)
    new = np.asarray(over)
    mask = np.asarray(layer)[:, :, 3] > 0
    ys, xs = np.nonzero(mask)
    if xs.min() < 300 or ys.min() < 232:
        raise SystemExit("label runs outside the reserved corner (x>=300, y>=232)")
    best, dist = gim._nearest(new[mask].reshape(-1, 4), pal)
    out_idx = np.frombuffer(bytes(idx), np.uint8).copy().reshape(H, W)
    out_idx[mask] = best
    white = int(np.argmin(((pal_arr[:, :3].astype(int) - 255) ** 2).sum(1)))
    black = int(np.argmin((pal_arr[:, :3].astype(int) ** 2).sum(1)))

    out = gim.encode_indexed(data, bytes(out_idx.reshape(-1)), pal)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "wb").write(out)
    print("title tag %r / %r: %d px changed in x %d-%d, y %d-%d; palette white %s, black %s; font %s"
          % (version, a.author, int(mask.sum()), xs.min(), xs.max(), ys.min(), ys.max(),
             tuple(pal[white]), tuple(pal[black]), os.path.basename(font_path)))
    print("wrote", a.out, "from", src)
    if a.preview:
        _, _, _, i2, p2 = gim.read_indexed(out)
        img = Image.fromarray(np.array(p2, np.uint8)[np.frombuffer(bytes(i2), np.uint8)].reshape(H, W, 4), "RGBA")
        img.resize((W * 2, H * 2), Image.NEAREST).save(a.preview)
        print("preview", a.preview)


if __name__ == "__main__":
    main()
