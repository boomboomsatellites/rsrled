class ConsoleOutput:
    def __init__(self, cfg):
        self.width = int(cfg.get('console', {}).get('frame_width_chars', 32))
    def show(self, message):
        print('+' + '-' * self.width + '+')
        print('|' + message.title[:self.width].center(self.width) + '|')
        print('|' + '-' * self.width + '|')
        print('|' + message.body[:self.width].ljust(self.width) + '|')
        print('+' + '-' * self.width + '+')
