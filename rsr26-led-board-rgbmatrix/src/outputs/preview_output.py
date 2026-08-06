from PIL import Image
from src.outputs.rgb_matrix_output import render_message_image, text_width
from src.display.marquee import MarqueeState


class PreviewOutput:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = MarqueeState()
        self.scroll = cfg.get('scroll', {})
        self.scale = cfg.get('preview', {}).get('scale', 6)

    def show(self, message):
        body = (message.body or '').replace('\n', ' ').replace('\r', ' ')
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
        img = img.resize((img.width * self.scale, img.height * self.scale), Image.NEAREST)
        img.show()
        return done
