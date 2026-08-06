from __future__ import annotations
from datetime import datetime, timedelta
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


_font_cache = {}


def get_cached_font(cfg, size):
    key = (size, tuple(cfg.get('rgb_matrix', {}).get('font_candidates', [])))
    if key not in _font_cache:
        _font_cache[key] = load_font(cfg, size)
    return _font_cache[key]


# === preview_output.py から import される ===
def render_message_image(cfg, message, scroll_offset=2):
    matrix_cfg = cfg.get('matrix', {})
    layout = cfg.get('layout', {})
    width = int(matrix_cfg.get('width', 128))
    height = int(matrix_cfg.get('height', 64))
    brightness = int(cfg.get('rgb_matrix', {}).get('brightness', matrix_cfg.get('brightness', 60)))
    brightness = min(brightness, select_brightness(cfg, datetime.now().time()))

    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    title_font = get_cached_font(cfg, int(layout.get('title_font_size', 12)))
    body_font = get_cached_font(cfg, int(layout.get('body_font_size', 16)))
    bold = int(layout.get('bold_px', 1))

    amber = _scale((255, 190, 45), brightness)
    white = _scale((255, 255, 255), brightness)
    gray = _scale((70, 70, 70), brightness)
    red = _scale((255, 80, 60), brightness)

    title_y = int(layout.get('title_y', 4))
    sep_y = int(layout.get('separator_y', 20))
    body_y = int(layout.get('body_y', 26))

    title = (message.title or '')[:20]
    body = (message.body or '').replace('\n', ' ').replace('\r', ' ')
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
            raise RuntimeError('rgbmatrix Python bindings are not available.') from e

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

        self._tw_cache = {}
        self._bg_cache = {}
        self._body_cache = {}

    def show(self, message):
        body = (message.body or '').replace('\n', ' ').replace('\r', ' ')
        panel_width = int(self.cfg.get('matrix', {}).get('width', 128))
        panel_height = int(self.cfg.get('matrix', {}).get('height', 64))

        if body not in self._tw_cache:
            self._tw_cache[body] = text_width(self.cfg, body)
        tw = self._tw_cache[body]

        key = f'{message.message_type}:{message.title}:{message.body}'
        offset, done = self.state.frame(
            key, tw, panel_width,
            step=int(self.scroll.get('step_pixels', 2)),
            end_hold=int(self.scroll.get('end_hold_frames', 20)),
            short_frames=int(self.scroll.get('short_message_frames', 60)),
        )

        img = self._render_fast(message, body, tw, offset, panel_width, panel_height)
        self.matrix.SetImage(img)
        return done

    def _render_fast(self, message, body, tw, offset, panel_width, panel_height):
        brightness = int(self.cfg.get('rgb_matrix', {}).get('brightness', 60))
        brightness = min(brightness, select_brightness(self.cfg, datetime.now().time()))
        layout = self.cfg.get('layout', {})
        bold = int(layout.get('bold_px', 1))
        body_font = get_cached_font(self.cfg, int(layout.get('body_font_size', 16)))
        title_font = get_cached_font(self.cfg, int(layout.get('title_font_size', 12)))
        body_y = int(layout.get('body_y', 26))

        # 背景は「黒+区切り線」だけ（メッセージに依存しない永続キャッシュ）
        bg_key = f"base_bg:{brightness}"
        if bg_key not in self._bg_cache:
            bg = Image.new('RGB', (panel_width, panel_height), 'black')
            draw = ImageDraw.Draw(bg)
            gray = _scale((70, 70, 70), brightness)
            sep_y = int(layout.get('separator_y', 20))
            draw.line((0, sep_y, panel_width, sep_y), fill=gray)
            self._bg_cache[bg_key] = bg

        # タイトル画像を別キャッシュ
        title = (message.title or '')[:20]
        title_key = f"title:{title}:{message.message_type}:{brightness}:{bold}"
        if title_key not in self._bg_cache:
            title_img = Image.new('RGB', (panel_width, panel_height), 'black')
            draw = ImageDraw.Draw(title_img)
            amber = _scale((255, 190, 45), brightness)
            red = _scale((255, 80, 60), brightness)
            title_color = red if message.message_type == 'caution' else amber
            title_y = int(layout.get('title_y', 4))
            draw_text_bold(draw, (2, title_y), title, title_color, title_font, bold=bold)
            self._bg_cache[title_key] = title_img

        # 本文キャッシュ：高さをタイトル下の領域だけに（panel_height - body_y）
        body_key = f"{body}:{bold}:{brightness}"
        body_h = panel_height - body_y
        if body_key not in self._body_cache:
            w = max(tw, panel_width) + panel_width
            body_img = Image.new('RGB', (w, body_h), 'black')
            draw = ImageDraw.Draw(body_img)
            white = _scale((255, 255, 255), brightness)
            # 本文画像内では y=0 から描画（貼り付け時に body_y へ）
            draw_text_bold(draw, (0, 0), body, white, body_font, bold=bold)
            self._body_cache[body_key] = body_img

        # 合成：背景 → タイトル → 本文
        result = self._bg_cache[bg_key].copy()
        result.paste(self._bg_cache[title_key], (0, 0))
        
        body_img = self._body_cache[body_key]
        if offset >= 0:
            paste_x = offset
            src_x = 0
            crop_width = min(panel_width - offset, body_img.width)
        else:
            paste_x = 0
            src_x = -offset
            crop_width = min(panel_width, body_img.width + offset)
        
        if crop_width > 0:
            cropped = body_img.crop((src_x, 0, src_x + crop_width, body_h))
            # y=body_y に貼り付け → タイトル部分は上書きされない
            result.paste(cropped, (paste_x, body_y))

        # 右下に投稿時刻（JST）を表示
        posted_at = getattr(message, 'posted_at', '')
        if posted_at:
            try:                
                dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                dt_jst = dt + timedelta(hours=9)
                time_str = dt_jst.strftime('%Y/%m/%d %H:%M:%S')
                
                time_font_size = 8
                time_font = get_cached_font(self.cfg, time_font_size)
                gray = _scale((120, 120, 120), brightness)
                
                # テキスト幅測定
                tw_time = text_width(self.cfg, time_str, time_font_size)
                time_x = panel_width - tw_time - 2
                time_y = panel_height - time_font_size - 2
                
                draw = ImageDraw.Draw(result)
                draw.text((time_x, time_y), time_str, fill=gray, font=time_font)
            except Exception:
                pass  # 時刻パース失敗時は無視
        
        return result
