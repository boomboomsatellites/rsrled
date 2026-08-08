from __future__ import annotations
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from src.display.brightness import select_brightness
from src.display.marquee import MarqueeState
from src.display.textdraw import load_font, draw_text_bold, has_font_for_text, measure_text_width
from src.display.text_normalize import normalize_display_text


def _scale(color, brightness):
    factor = max(0, min(int(brightness), 100)) / 100
    return tuple(int(c * factor) for c in color)


# タイトル用カラーパレット（黒背景で視認性の良い10色）
TITLE_COLOR_PALETTE = [
    (255, 190, 45),   # amber
    (0, 220, 220),    # cyan
    (255, 60, 220),   # magenta
    (140, 255, 60),   # lime
    (255, 120, 40),   # orange
    (60, 160, 255),   # sky blue
    (255, 90, 150),   # pink
    (255, 230, 60),   # yellow
    (170, 90, 255),   # purple
    (60, 255, 180),   # mint
]


def _pick_title_color(message):
    """投稿内容から決定的にパレットの色を選ぶ（同じ投稿は常に同じ色）。"""
    key = f'{message.title}:{message.body}:{getattr(message, "posted_at", "")}'
    idx = hash(key) % len(TITLE_COLOR_PALETTE)
    return TITLE_COLOR_PALETTE[idx]

_normalized_text_cache = {}
_text_width_cache = {}


def _normalize_for_size(cfg, text, size):
    display_cfg = cfg.get('display', {})
    key = (
        size,
        tuple(cfg.get('rgb_matrix', {}).get('font_candidates', [])),
        bool(display_cfg.get('emoji_demojize', True)),
        str(display_cfg.get('emoji_demojize_mode', 'missing_only')).lower(),
        text,
    )
    cached = _normalized_text_cache.get(key)
    if cached is not None:
        return cached

    normalized = normalize_display_text(
        text,
        cfg,
        can_render_emoji=lambda token: has_font_for_text(cfg, size, token),
    )
    _normalized_text_cache[key] = normalized
    return normalized


def text_width(cfg, text, font_size=None):
    size = font_size or int(cfg.get('layout', {}).get('body_font_size', 16))
    text = text or ''
    key = (
        size,
        tuple(cfg.get('rgb_matrix', {}).get('font_candidates', [])),
        tuple(sorted((cfg.get('display', {}) or {}).items())),
        text,
    )
    cached = _text_width_cache.get(key)
    if cached is not None:
        return cached

    normalized = _normalize_for_size(cfg, text, size)
    width = measure_text_width(cfg, normalized, size)
    _text_width_cache[key] = width
    return width


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

    title_size = int(layout.get('title_font_size', 12))
    body_size = int(layout.get('body_font_size', 16))
    title = _normalize_for_size(cfg, (message.title or '')[:20], title_size)
    body = _normalize_for_size(cfg, (message.body or '').replace('\n', ' ').replace('\r', ' '), body_size)
    title_color = red if message.message_type == 'caution' else _scale(_pick_title_color(message), brightness)

    draw_text_bold(draw, (2, title_y), title, title_color, title_font, bold=bold, cfg=cfg, font_size=title_size)
    draw.line((0, sep_y, width, sep_y), fill=gray)
    draw_text_bold(draw, (scroll_offset, body_y), body, white, body_font, bold=bold, cfg=cfg, font_size=body_size)
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
        body_size = int(self.cfg.get('layout', {}).get('body_font_size', 16))
        body = _normalize_for_size(self.cfg, (message.body or '').replace('\n', ' ').replace('\r', ' '), body_size)
        panel_width = int(self.cfg.get('matrix', {}).get('width', 128))
        panel_height = int(self.cfg.get('matrix', {}).get('height', 64))

        tw_key = (body_size, body)
        if tw_key not in self._tw_cache:
            self._tw_cache[tw_key] = measure_text_width(self.cfg, body, body_size)
        tw = self._tw_cache[tw_key]

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

    def show_image(self, image):
        self.matrix.SetImage(image)
        return True

    def _render_fast(self, message, body, tw, offset, panel_width, panel_height):
        brightness = int(self.cfg.get('rgb_matrix', {}).get('brightness', 60))
        brightness = min(brightness, select_brightness(self.cfg, datetime.now().time()))
        layout = self.cfg.get('layout', {})
        bold = int(layout.get('bold_px', 1))
        body_size = int(layout.get('body_font_size', 16))
        title_size = int(layout.get('title_font_size', 12))
        body_font = get_cached_font(self.cfg, body_size)
        title_font = get_cached_font(self.cfg, title_size)
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

        # タイトル画像を別キャッシュ（投稿ごとに色が変わるため、色決定キーもキャッシュキーに含める）
        title = _normalize_for_size(self.cfg, (message.title or '')[:20], title_size)
        title_color_key = _pick_title_color(message)
        title_key = f"title:{title}:{message.message_type}:{brightness}:{bold}:{title_color_key}"
        if title_key not in self._bg_cache:
            title_img = Image.new('RGB', (panel_width, panel_height), 'black')
            draw = ImageDraw.Draw(title_img)
            red = _scale((255, 80, 60), brightness)
            title_color = red if message.message_type == 'caution' else _scale(title_color_key, brightness)
            title_y = int(layout.get('title_y', 4))
            draw_text_bold(draw, (2, title_y), title, title_color, title_font, bold=bold, cfg=self.cfg, font_size=title_size)
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
            draw_text_bold(draw, (0, 0), body, white, body_font, bold=bold, cfg=self.cfg, font_size=body_size)
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
            time_key = f"time_str:{posted_at}"
            if time_key not in self._bg_cache:
                try:
                    dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                    dt_jst = dt + timedelta(hours=9)
                    self._bg_cache[time_key] = dt_jst.strftime('%Y/%m/%d %H:%M:%S')
                except Exception:
                    self._bg_cache[time_key] = None
            
            time_str = self._bg_cache[time_key]
            if time_str:
                time_font_size = 8
                time_font = get_cached_font(self.cfg, time_font_size)
                gray = _scale((120, 120, 120), brightness)
                tw_time = text_width(self.cfg, time_str, time_font_size)
                time_x = panel_width - tw_time - 2
                time_y = panel_height - time_font_size - 3
                draw = ImageDraw.Draw(result)
                draw.text((time_x, time_y), time_str, fill=gray, font=time_font)
        
        return result
