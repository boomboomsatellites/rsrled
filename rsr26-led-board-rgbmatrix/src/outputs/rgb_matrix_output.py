from __future__ import annotations
from datetime import datetime
from PIL import Image, ImageDraw
from src.display.brightness import select_brightness
from src.display.marquee import MarqueeState
from src.display.textdraw import load_font, draw_text_bold


def _scale(color, brightness):
    factor = max(0, min(int(brightness), 100)) / 100
    return tuple(int(c * factor) for c in color)


def text_width(cfg, text, font_size=None):
    font = load_font(cfg, font_size or int(cfg.get('layout', {}).get('body_font_size', 16)))
    img = Image.new('RGB', (1, 1), 'black')
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text or '', font=font)
    return bbox[2] - bbox[0]


def render_message_image(cfg, message, scroll_offset=2):
    matrix_cfg = cfg.get('matrix', {})
    layout = cfg.get('layout', {})
    width = int(matrix_cfg.get('width', 128))
    height = int(matrix_cfg.get('height', 64))
    brightness = int(cfg.get('rgb_matrix', {}).get('brightness', matrix_cfg.get('brightness', 60)))
    brightness = min(brightness, select_brightness(cfg, datetime.now().time()))

    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    title_font = load_font(cfg, int(layout.get('title_font_size', 12)))
    body_font = load_font(cfg, int(layout.get('body_font_size', 16)))
    bold = int(layout.get('bold_px', 1))

    amber = _scale((255, 190, 45), brightness)
    white = _scale((255, 255, 255), brightness)
    gray = _scale((70, 70, 70), brightness)
    red = _scale((255, 80, 60), brightness)

    title_y = int(layout.get('title_y', 4))
    sep_y = int(layout.get('separator_y', 20))
    body_y = int(layout.get('body_y', 26))

    title = (message.title or '')[:20]
    body = message.body or ''
    title_color = red if message.message_type == 'caution' else amber

    draw_text_bold(draw, (2, title_y), title, title_color, title_font, bold=bold)
    draw.line((0, sep_y, width, sep_y), fill=gray)
    draw_text_bold(draw, (scroll_offset, body_y), body, white, body_font, bold=bold)
    return img


class RGBMatrixOutput:
    def __init__(self, cfg):
        self.cfg = cfg
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
        except Exception as e:
            raise RuntimeError('rgbmatrix Python bindings are not available. Install rpi-rgb-led-matrix bindings first.') from e

        rgb = cfg.get('rgb_matrix', {})
        matrix_cfg = cfg.get('matrix', {})
        options = RGBMatrixOptions()
        options.rows = int(rgb.get('rows', matrix_cfg.get('height', 64)))
        options.cols = int(rgb.get('cols', matrix_cfg.get('width', 128)))
        options.chain_length = int(rgb.get('chain_length', 1))
        options.parallel = int(rgb.get('parallel', 1))
        options.hardware_mapping = str(rgb.get('hardware_mapping', 'regular'))
        options.gpio_slowdown = int(rgb.get('gpio_slowdown', 3))
        options.brightness = int(rgb.get('brightness', matrix_cfg.get('brightness', 60)))
        options.disable_hardware_pulsing = bool(rgb.get('disable_hardware_pulsing', True))
        options.multiplexing = int(rgb.get('multiplexing', 0))
        options.pwm_bits = int(rgb.get('pwm_bits', 8))
        options.led_rgb_sequence = str(rgb.get('led_rgb_sequence', 'RGB'))
        options.show_refresh_rate = bool(rgb.get('show_refresh_rate', False))
        self.matrix = RGBMatrix(options=options)
        self.state = MarqueeState()
        self.scroll = cfg.get('scroll', {})

    def show(self, message):
        body = message.body or ''
        panel_width = int(self.cfg.get('matrix', {}).get('width', 128))
        tw = text_width(self.cfg, body)
        key = f'{message.message_type}:{message.title}:{message.body}'
        offset, done = self.state.frame(
            key, tw, panel_width,
            step=int(self.scroll.get('step_pixels', 2)),
            end_hold=int(self.scroll.get('end_hold_frames', 20)),
            short_frames=int(self.scroll.get('short_message_frames', 60)),
        )
        img = render_message_image(self.cfg, message, scroll_offset=offset)
        self.matrix.SetImage(img.convert('RGB'))
        return done
