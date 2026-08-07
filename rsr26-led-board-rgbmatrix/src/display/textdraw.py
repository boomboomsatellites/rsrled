from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import emoji
except Exception:
    emoji = None


_font_list_cache = {}
_missing_sig_cache = {}


def load_fonts(cfg, size):
    key = (size, tuple(cfg.get('rgb_matrix', {}).get('font_candidates', [])))
    if key in _font_list_cache:
        return _font_list_cache[key]

    fonts = []
    candidates = list(cfg.get('rgb_matrix', {}).get('font_candidates', []))
    for path in candidates:
        if path and Path(path).exists():
            try:
                fonts.append(ImageFont.truetype(path, size))
            except Exception:
                pass
    if not fonts:
        fonts.append(ImageFont.load_default())

    _font_list_cache[key] = fonts
    return fonts


def load_font(cfg, size):
    return load_fonts(cfg, size)[0]


def _glyph_signature(font, text):
    try:
        mask = font.getmask(text, mode='L')
        raw = bytes(mask)
        return (mask.size, hash(raw))
    except Exception:
        return None


def _missing_signature(font):
    key = id(font)
    if key not in _missing_sig_cache:
        _missing_sig_cache[key] = _glyph_signature(font, '\u0378')
    return _missing_sig_cache[key]


def font_supports_text(font, text):
    if not text:
        return True
    if text.isspace():
        return True
    sig = _glyph_signature(font, text)
    if sig is None:
        return False
    missing_sig = _missing_signature(font)
    if missing_sig is None:
        return True
    return sig != missing_sig


def has_font_for_text(cfg, size, text):
    for font in load_fonts(cfg, size):
        if font_supports_text(font, text):
            return True
    return False


def _emoji_spans(text):
    if emoji is None:
        return []
    try:
        return [
            (item['match_start'], item['match_end'], item['emoji'])
            for item in emoji.emoji_list(text)
        ]
    except Exception:
        return []


def _iter_tokens(text):
    spans = _emoji_spans(text)
    i = 0
    si = 0
    while i < len(text):
        if si < len(spans) and i == spans[si][0]:
            start, end, token = spans[si]
            yield token
            i = end
            si += 1
            continue
        yield text[i]
        i += 1


def _pick_font(cfg, size, token):
    fonts = load_fonts(cfg, size)
    for font in fonts:
        if font_supports_text(font, token):
            return font
    return fonts[0]


def _token_width(draw, token, font):
    bbox = draw.textbbox((0, 0), token, font=font)
    return max(0, bbox[2] - bbox[0])


def measure_text_width(cfg, text, size):
    if not text:
        return 0
    img = Image.new('RGB', (1, 1), 'black')
    draw = ImageDraw.Draw(img)
    width = 0
    for token in _iter_tokens(text):
        token_font = _pick_font(cfg, size, token)
        width += _token_width(draw, token, token_font)
    return width


def draw_text_bold(draw, xy, text, fill, font, bold=1, cfg=None, font_size=None):
    x, y = xy
    if cfg is None or font_size is None:
        for dx in range(max(0, bold) + 1):
            draw.text((x + dx, y), text, fill=fill, font=font)
        return

    cursor_x = x
    for token in _iter_tokens(text):
        token_font = _pick_font(cfg, font_size, token)
        for dx in range(max(0, bold) + 1):
            draw.text((cursor_x + dx, y), token, fill=fill, font=token_font)
        cursor_x += _token_width(draw, token, token_font)
