from src.display.marquee import MarqueeState

class ConsoleOutput:
    def __init__(self, cfg):
        self.width = int(cfg.get('console', {}).get('frame_width_chars', 32))
        self.state = MarqueeState()
        self.scroll = cfg.get('scroll', {})

    def show(self, message):
        key = f'{message.message_type}:{message.title}:{message.body}'
        # approximate text width in console chars
        x, done = self.state.frame(
            key, len(message.body), self.width,
            step=1,
            end_hold=int(self.scroll.get('end_hold_frames', 20)),
            short_frames=int(self.scroll.get('short_message_frames', 60)),
        )
        if len(message.body) > self.width:
            start = max(0, self.width - x) if x > 0 else abs(x)
            body = message.body[start:start+self.width]
        else:
            body = message.body
        print('+' + '-' * self.width + '+')
        print('|' + message.title[:self.width].center(self.width) + '|')
        print('|' + '-' * self.width + '|')
        print('|' + body[:self.width].ljust(self.width) + '|')
        print('+' + '-' * self.width + '+')
        return done
