from __future__ import annotations

from datetime import datetime
from pathlib import Path
from src.display.brightness import select_brightness
from src.display.scroller import PixelTextScroller


def _load_font(cfg: dict, size: int):
    from PIL import ImageFont
    candidates = list(cfg.get('rgb_matrix', {}).get('font_candidates', []))
    candidates += [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for path in candidates:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _scale(color, brightness: int):
    factor = max(0, min(int(brightness), 100)) / 100
    return tuple(int(c * factor) for c in color)


def render_message_image(cfg: dict, message, scroll_offset: int = 2):
    from PIL import Image, ImageDraw
    matrix_cfg = cfg.get('matrix', {})
    w = int(matrix_cfg.get('width', 128))
    h = int(matrix_cfg.get('height', 64))
    brightness = int(cfg.get('rgb_matrix', {}).get('brightness', matrix_cfg.get('brightness', 20)))
    brightness = min(brightness, select_brightness(cfg, datetime.now().time()))

    img = Image.new('RGB', (w, h), 'black')
    draw = ImageDraw.Draw(img)
    title_font = _load_font(cfg, int(cfg.get('layout', {}).get('title_font_size', 10)))
    body_font = _load_font(cfg, int(cfg.get('layout', {}).get('body_font_size', 9)))

    amber = _scale((255, 180, 40), brightness)
    green = _scale((80, 255, 120), brightness)
    gray = _scale((70, 70, 70), brightness)
    red = _scale((255, 80, 60), brightness)

    title_color = red if message.message_type == 'caution' else amber
    draw.text((2, 1), (message.title or '')[:20], fill=title_color, font=title_font)
    draw.line((0, 15, w, 15), fill=gray)
    draw.text((scroll_offset, 22), message.body or '', fill=green, font=body_font)
    return img


class RGBMatrixOutput:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
        except Exception as e:
            raise RuntimeError(
                'rgbmatrix Python bindings are not available. '
                'Build/install rpi-rgb-led-matrix Python bindings, then run with sudo if needed.'
            ) from e

        rgb_cfg = cfg.get('rgb_matrix', {})
        matrix_cfg = cfg.get('matrix', {})
        options = RGBMatrixOptions()
        options.rows = int(rgb_cfg.get('rows', matrix_cfg.get('height', 64)))
        options.cols = int(rgb_cfg.get('cols', matrix_cfg.get('width', 128)))
        options.chain_length = int(rgb_cfg.get('chain_length', 1))
        options.parallel = int(rgb_cfg.get('parallel', 1))
        options.hardware_mapping = str(rgb_cfg.get('hardware_mapping', 'regular'))
        options.gpio_slowdown = int(rgb_cfg.get('gpio_slowdown', 3))
        options.brightness = int(rgb_cfg.get('brightness', matrix_cfg.get('brightness', 20)))
        options.disable_hardware_pulsing = bool(rgb_cfg.get('disable_hardware_pulsing', True))
        options.multiplexing = int(rgb_cfg.get('multiplexing', 0))
        options.pwm_bits = int(rgb_cfg.get('pwm_bits', 8))
        options.led_rgb_sequence = str(rgb_cfg.get('led_rgb_sequence', 'RGB'))
        options.show_refresh_rate = bool(rgb_cfg.get('show_refresh_rate', False))

        self.matrix = RGBMatrix(options=options)
        self.scroller = PixelTextScroller()

    def show(self, message):
        from PIL import Image, ImageDraw
        font = _load_font(self.cfg, int(self.cfg.get('layout', {}).get('body_font_size', 9)))
        tmp = Image.new('RGB', (1, 1), 'black')
        d = ImageDraw.Draw(tmp)
        body = message.body or ''
        bbox = d.textbbox((0, 0), body, font=font)
        text_width = bbox[2] - bbox[0]
        panel_width = int(self.cfg.get('matrix', {}).get('width', 128))
        key = f'{message.message_type}:{message.title}:{message.body}'
        offset = self.scroller.offset(key, text_width, panel_width, step=2)
        img = render_message_image(self.cfg, message, scroll_offset=offset)
        self.matrix.SetImage(img.convert('RGB'))
