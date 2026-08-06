class PixelTextScroller:
    def __init__(self):
        self.offsets = {}
    def offset(self, key, text_width, panel_width, step=2):
        if text_width <= panel_width:
            return 2
        max_offset = text_width + panel_width
        cur = self.offsets.get(key, 0)
        self.offsets[key] = (cur + step) % max_offset
        return panel_width - cur
