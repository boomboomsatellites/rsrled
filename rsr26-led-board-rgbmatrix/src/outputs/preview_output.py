from src.outputs.rgb_matrix_output import render_message_image

class PreviewOutput:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = 'preview_frame.png'
    def show(self, message):
        scale = int(self.cfg.get('preview', {}).get('scale', 6))
        img = render_message_image(self.cfg, message, scroll_offset=2)
        img.resize((img.width * scale, img.height * scale)).save(self.path)
        print(f'preview saved: {self.path} [{message.title}] {message.body}')
