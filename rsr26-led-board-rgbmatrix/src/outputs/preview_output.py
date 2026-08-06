from src.outputs.rgb_matrix_output import render_message_image, text_width
from src.display.marquee import MarqueeState

class PreviewOutput:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = 'preview_frame.png'
        self.state = MarqueeState()
        self.scroll = cfg.get('scroll', {})

    def show(self, message):
        panel_width = int(self.cfg.get('matrix', {}).get('width', 128))
        tw = text_width(self.cfg, message.body or '')
        key = f'{message.message_type}:{message.title}:{message.body}'
        offset, done = self.state.frame(
            key, tw, panel_width,
            step=int(self.scroll.get('step_pixels', 2)),
            end_hold=int(self.scroll.get('end_hold_frames', 20)),
            short_frames=int(self.scroll.get('short_message_frames', 60)),
        )
        img = render_message_image(self.cfg, message, scroll_offset=offset)
        scale = int(self.cfg.get('preview', {}).get('scale', 6))
        img.resize((img.width * scale, img.height * scale)).save(self.path)
        print(f'preview saved: {self.path} done={done} [{message.title}]')
        return done
