from pathlib import Path

def load_font(cfg, size):
    from PIL import ImageFont
    candidates = list(cfg.get('rgb_matrix', {}).get('font_candidates', []))
    for path in candidates:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_text_bold(draw, xy, text, fill, font, bold=1):
    x, y = xy
    for dx in range(max(0, bold) + 1):
        draw.text((x + dx, y), text, fill=fill, font=font)
