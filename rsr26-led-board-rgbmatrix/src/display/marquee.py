class MarqueeState:
    """Per-message state.

    Returns an x offset and True only after the current message has fully scrolled
    across the panel and completed an end-hold period.
    """
    def __init__(self):
        self.positions = {}
        self.short_counts = {}

    def frame(self, key, text_width, panel_width, *, step=2, end_hold=20, short_frames=60):
        visible_width = max(1, panel_width - 4)
        if text_width <= visible_width:
            count = self.short_counts.get(key, 0) + 1
            self.short_counts[key] = count
            done = count >= short_frames
            if done:
                self.short_counts.pop(key, None)
                self.positions.pop(key, None)
            return 2, done

        pos = self.positions.get(key, 0)
        # Start off-screen right, travel fully left until text tail exits, then hold.
        travel = panel_width + text_width
        total = travel + end_hold
        x = panel_width - pos if pos < travel else -text_width
        pos += step
        done = pos >= total
        if done:
            self.positions.pop(key, None)
            self.short_counts.pop(key, None)
        else:
            self.positions[key] = pos
        return x, done
