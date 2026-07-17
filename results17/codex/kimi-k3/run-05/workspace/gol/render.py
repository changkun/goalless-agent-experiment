"""Render simulation runs as titled poster PNGs, pure stdlib."""
from __future__ import annotations

from . import palettes
from .png import write_png


def _blank(width, height, color):
    row = bytearray(bytes(color) * width)
    return [bytearray(row) for _ in range(height)]


def _fill_rect(pixels, img_w, img_h, x, y, w, h, color):
    fill = bytes(color)
    for py in range(max(0, y), min(img_h, y + h)):
        row = pixels[py]
        for px in range(max(0, x), min(img_w, x + w)):
            row[px * 3:px * 3 + 3] = fill


def render_frame(grid, ages, palette, cell_px, pad):
    """Render one generation. `ages[y*w+x]` holds ticks-since-birth,
    which drives the color ramp: young cells glow dim, elders burn bright."""
    img_w = grid.w * cell_px + pad * 2
    img_h = grid.h * cell_px + pad * 2
    pixels = _blank(img_w, img_h, palette["bg"])
    ramp = palette["ramp"]
    if cell_px >= 6:
        line = palette["grid"]
        for gy in range(grid.h + 1):
            y = pad + gy * cell_px
            _fill_rect(pixels, img_w, img_h, pad, y, grid.w * cell_px, 1, line)
        for gx in range(grid.w + 1):
            x = pad + gx * cell_px
            _fill_rect(pixels, img_w, img_h, x, pad, 1, grid.h * cell_px, line)
    inset = 1 if cell_px >= 4 else 0
    for gy in range(grid.h):
        for gx in range(grid.w):
            idx = gy * grid.w + gx
            if not grid.cells[idx]:
                continue
            age = ages[idx]
            t = min(1.0, age / 12.0)
            pos = t * (len(ramp) - 1)
            lo = int(pos)
            hi = min(len(ramp) - 1, lo + 1)
            color = palettes.lerp(ramp[lo], ramp[hi], pos - lo)
            _fill_rect(
                pixels, img_w, img_h,
                pad + gx * cell_px + inset,
                pad + gy * cell_px + inset,
                cell_px - 2 * inset,
                cell_px - 2 * inset,
                color,
            )
    return pixels, img_w, img_h


def _stack_vertical(frames, gap, bg):
    img_w = max(f[1] for f in frames)
    img_h = sum(f[2] for f in frames) + gap * (len(frames) - 1)
    pixels = _blank(img_w, img_h, bg)
    y = 0
    for frame_px, fw, fh in frames:
        for row_i in range(fh):
            pixels[y + row_i][:fw * 3] = frame_px[row_i]
        y += fh + gap
    return pixels, img_w, img_h


def _title_bar(pixels, img_w, img_h, palette, title, subtitle):
    scale = 3 if img_w >= 420 else 2
    tw, th = palettes.text_size(title, scale)
    x = max(8, (img_w - tw) // 2)
    palettes.draw_text(pixels, img_w, img_h, title, x, 12, palette["text"], scale)
    if subtitle:
        s_scale = max(1, scale - 1)
        sw, sh = palettes.text_size(subtitle, s_scale)
        sx = max(8, (img_w - sw) // 2)
        palettes.draw_text(
            pixels, img_w, img_h, subtitle, sx, 12 + th + 6,
            palette["subtext"], s_scale,
        )
        return th + sh + 28
    return th + 22


def render_poster(sim, frames_spec, path, palette_name="phosphor",
                  cell_px=10, title="LIFE", subtitle=""):
    """Run the sim, capturing a snapshot after each advance in
    `frames_spec`, then write a titled poster PNG.

    Returns the list of captured tick numbers."""
    palette = palettes.PALETTES[palette_name]
    pad = max(4, cell_px)
    ages = bytearray(sim.grid.w * sim.grid.h)
    captured = []
    for advance in frames_spec:
        for _ in range(advance):
            sim.step()
            cells = sim.grid.cells
            for i in range(len(ages)):
                ages[i] = ages[i] + 1 if cells[i] else 0
        pixels, fw, fh = render_frame(sim.grid, ages, palette, cell_px, pad)
        captured.append((sim.tick_count, (pixels, fw, fh)))
    body_px, img_w, body_h = _stack_vertical(
        [f for _, f in captured], gap=max(6, cell_px), bg=palette["bg"]
    )
    header_h = _title_bar(
        _blank(img_w, 1, palette["bg"]), img_w, 1, palette, title, subtitle
    )
    footer_h = 30
    img_h = header_h + body_h + footer_h
    pixels = _blank(img_w, img_h, palette["bg"])
    _title_bar(pixels, img_w, img_h, palette, title, subtitle)
    for row_i in range(body_h):
        pixels[header_h + row_i] = body_px[row_i]
    tick_text = "TICKS " + "  ".join(str(t) for t, _ in captured)
    sw, _ = palettes.text_size(tick_text, 1)
    palettes.draw_text(
        pixels, img_w, img_h, tick_text,
        max(8, (img_w - sw) // 2), img_h - 18,
        palette["subtext"], 1,
    )
    write_png(path, img_w, img_h, pixels)
    return [t for t, _ in captured]
