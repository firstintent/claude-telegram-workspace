#!/usr/bin/env python3
"""cct-snapshot — render the current tmux pane to a PNG.

Captures the active pane via `tmux capture-pane -e -p`, parses a useful subset of
ANSI SGR (foreground/background/bold, 16/256/truecolor), and renders the result to
a PNG with Pillow. Refuses if $TMUX is unset.

Two-tier font dispatch: JetBrains Mono (vendored) for Latin/symbols/box-drawing,
WenQuanYi Zen Hei (system) for CJK. Each segment advances by its font's natural
width — columns won't grid-align across tiers, but ASCII rendering is much cleaner
than wqy index 1.

Usage:
    cct_snapshot.py
    cct_snapshot.py --out /tmp/snap.png
    cct_snapshot.py --history 200
    cct_snapshot.py --no-color

Output: JSON on stdout `{ok, session, path, width, height}`.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent

FONT_LATIN = str(_SKILL_DIR / "fonts" / "JetBrainsMono-Regular.ttf")
FONT_CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT_CJK_INDEX = 1  # ttc index 1 = "WenQuanYi Zen Hei Mono"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE = 14
PAD = 6

BG_DEFAULT = (24, 24, 27)
FG_DEFAULT = (220, 220, 220)

ANSI_NORMAL = [
    (0, 0, 0),
    (205, 49, 49),
    (13, 188, 121),
    (229, 229, 16),
    (36, 114, 200),
    (188, 63, 188),
    (17, 168, 205),
    (229, 229, 229),
]
ANSI_BRIGHT = [
    (102, 102, 102),
    (241, 76, 76),
    (35, 209, 139),
    (245, 245, 67),
    (59, 142, 234),
    (214, 112, 214),
    (41, 184, 219),
    (255, 255, 255),
]

ANSI_RE = re.compile(r"\x1b\[([0-9;]*)([a-zA-Z])")


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def current_pane_and_session():
    if not os.environ.get("TMUX") or not os.environ.get("TMUX_PANE"):
        fail(
            "当前 Claude 进程不在 tmux 内（$TMUX 或 $TMUX_PANE 未设置）。"
            "cct-snapshot 仅在 tmux 中运行的 Claude 会话内可用。"
        )
    pane = os.environ["TMUX_PANE"]
    try:
        out = subprocess.run(
            ["tmux", "display-message", "-t", pane, "-p", "#{session_name}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        fail(f"tmux display-message 失败: {(e.stderr or '').strip()}")
    if not out:
        fail("无法从 tmux 获取当前 session 名。")
    return pane, out


def is_cjk(ch):
    cp = ord(ch)
    return (
        0x2E80 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0xFE30 <= cp <= 0xFE4F
        or 0xFF00 <= cp <= 0xFFEF
        or 0x3000 <= cp <= 0x303F
    )


def palette_256(n):
    if n < 8:
        return ANSI_NORMAL[n]
    if n < 16:
        return ANSI_BRIGHT[n - 8]
    if n < 232:
        n -= 16
        r, g, b = n // 36, (n // 6) % 6, n % 6
        levels = [0, 95, 135, 175, 215, 255]
        return (levels[r], levels[g], levels[b])
    v = 8 + (n - 232) * 10
    return (v, v, v)


def apply_sgr(state, params):
    if not params:
        params = "0"
    parts = [int(p) if p else 0 for p in params.split(";")]
    i = 0
    while i < len(parts):
        p = parts[i]
        if p == 0:
            state["fg"] = FG_DEFAULT
            state["bg"] = BG_DEFAULT
            state["bold"] = False
        elif p == 1:
            state["bold"] = True
        elif p == 22:
            state["bold"] = False
        elif 30 <= p <= 37:
            colors = ANSI_BRIGHT if state["bold"] else ANSI_NORMAL
            state["fg"] = colors[p - 30]
        elif 40 <= p <= 47:
            state["bg"] = ANSI_NORMAL[p - 40]
        elif 90 <= p <= 97:
            state["fg"] = ANSI_BRIGHT[p - 90]
        elif 100 <= p <= 107:
            state["bg"] = ANSI_BRIGHT[p - 100]
        elif p == 38 and i + 2 < len(parts) and parts[i + 1] == 5:
            state["fg"] = palette_256(parts[i + 2])
            i += 2
        elif p == 38 and i + 4 < len(parts) and parts[i + 1] == 2:
            state["fg"] = (parts[i + 2], parts[i + 3], parts[i + 4])
            i += 4
        elif p == 48 and i + 2 < len(parts) and parts[i + 1] == 5:
            state["bg"] = palette_256(parts[i + 2])
            i += 2
        elif p == 48 and i + 4 < len(parts) and parts[i + 1] == 2:
            state["bg"] = (parts[i + 2], parts[i + 3], parts[i + 4])
            i += 4
        elif p == 39:
            state["fg"] = FG_DEFAULT
        elif p == 49:
            state["bg"] = BG_DEFAULT
        i += 1


def parse_ansi(text, color=True):
    rows = [[]]
    state = {"fg": FG_DEFAULT, "bg": BG_DEFAULT, "bold": False}
    i = 0
    while i < len(text):
        m = ANSI_RE.match(text, i)
        if m:
            params, fn = m.group(1), m.group(2)
            if color and fn == "m":
                apply_sgr(state, params)
            i = m.end()
            continue
        ch = text[i]
        i += 1
        if ch == "\n":
            rows.append([])
        elif ch == "\r":
            pass
        elif ord(ch) < 32:
            pass
        else:
            rows[-1].append((ch, state["fg"], state["bg"], state["bold"]))
    return rows


def capture_pane(target, history, color):
    args = ["tmux", "capture-pane", "-t", target, "-p"]
    if color:
        args.append("-e")
    if history > 0:
        args.extend(["-S", f"-{history}"])
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        fail(f"tmux capture-pane 失败: {(e.stderr or '').strip()}")


def _row_to_segments(row):
    """Group consecutive cells with the same (fg, bg, bold, font_tier) into segments."""
    if not row:
        return []
    segs = []
    chars = [row[0][0]]
    fg, bg, bold = row[0][1], row[0][2], row[0][3]
    tier = 1 if is_cjk(row[0][0]) else 0
    for ch, f, b, bd in row[1:]:
        t = 1 if is_cjk(ch) else 0
        if (f, b, bd, t) == (fg, bg, bold, tier):
            chars.append(ch)
        else:
            segs.append(("".join(chars), fg, bg, bold, tier))
            chars = [ch]
            fg, bg, bold, tier = f, b, bd, t
    segs.append(("".join(chars), fg, bg, bold, tier))
    return segs


def make_image(rows, out_path, scale=1.0):
    from PIL import Image, ImageDraw, ImageFont

    font_size = max(8, int(round(FONT_SIZE * scale)))
    try:
        latin = ImageFont.truetype(FONT_LATIN, font_size)
    except OSError:
        latin = ImageFont.truetype(FONT_FALLBACK, font_size)
    try:
        cjk = ImageFont.truetype(FONT_CJK, font_size, index=FONT_CJK_INDEX)
    except OSError:
        cjk = latin
    fonts = (latin, cjk)

    # Tight line height: take the larger of the two fonts' rendered glyph
    # extents and add 1px leading. Avoids descender clipping while staying
    # much tighter than ascent+descent's typographic box.
    latin_bbox = latin.getbbox("AgQpyj")
    cjk_bbox = cjk.getbbox("中文一g")
    line_h = max(font_size + 1, latin_bbox[3] + 1, cjk_bbox[3] + 1)
    pad = max(3, int(round(PAD * scale)))

    if not any(rows):
        rows = [[(" ", FG_DEFAULT, BG_DEFAULT, False)]]

    # Pre-segment all rows; reuse for both width measurement and drawing.
    all_segs = [_row_to_segments(row) for row in rows]

    max_w = 0.0
    for segs in all_segs:
        w = 0.0
        for text, _fg, _bg, _bold, tier in segs:
            w += fonts[tier].getlength(text)
        if w > max_w:
            max_w = w

    width = int(round(max_w)) + 2 * pad
    height = len(rows) * line_h + 2 * pad

    img = Image.new("RGB", (width, height), BG_DEFAULT)
    draw = ImageDraw.Draw(img)

    y = pad
    for segs in all_segs:
        x = float(pad)
        for text, fg, bg, _bold, tier in segs:
            font = fonts[tier]
            seg_w = font.getlength(text)
            x_int = int(round(x))
            x_end = int(round(x + seg_w))
            if bg != BG_DEFAULT:
                draw.rectangle([x_int, y, x_end, y + line_h], fill=bg)
            if text.strip():
                draw.text((x_int, y), text, fill=fg, font=font)
            x += seg_w
        y += line_h

    # Quantize to a 256-color palette PNG. Terminal output uses few distinct
    # colors, so an adaptive palette preserves the look while shrinking the
    # file ~3-5x vs 24-bit RGB. dither=0 keeps text edges crisp.
    img = img.quantize(colors=256, dither=0)
    img.save(out_path, optimize=True, compress_level=9)
    return img.size


def main():
    parser = argparse.ArgumentParser(description="Render the current tmux pane to a PNG.")
    parser.add_argument("--out", default=None,
                        help="output PNG path (default: /tmp/cct-snapshot-<session>-<ts>.png)")
    parser.add_argument("--history", type=int, default=0,
                        help="lines of scrollback to include (default 0 = visible only)")
    parser.add_argument("--no-color", action="store_true",
                        help="render plain monochrome (skip ANSI parsing)")
    parser.add_argument("--scale", type=float, default=0.75,
                        help="scale factor for output image (default: 0.75)")
    args = parser.parse_args()

    pane, session = current_pane_and_session()
    text = capture_pane(pane, args.history, color=not args.no_color)
    rows = parse_ansi(text, color=not args.no_color)

    out_path = args.out or os.path.join(
        tempfile.gettempdir(),
        f"cct-snapshot-{session}-{time.time_ns()}.png",
    )
    size = make_image(rows, out_path, scale=args.scale)

    print(json.dumps({
        "ok": True,
        "session": session,
        "pane": pane,
        "path": out_path,
        "width": size[0],
        "height": size[1],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
