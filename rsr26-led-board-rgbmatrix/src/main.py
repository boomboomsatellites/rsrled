import argparse, time
from src.config import load_config
from src.collectors.mock_collector import MockCollector
from src.analyzers.message_builder import build_messages
from src.outputs.console_output import ConsoleOutput
from src.outputs.preview_output import PreviewOutput
from src.outputs.rgb_matrix_output import RGBMatrixOutput

def make_output(name, cfg):
    if name == 'console': return ConsoleOutput(cfg)
    if name == 'preview': return PreviewOutput(cfg)
    if name == 'rgb_matrix': return RGBMatrixOutput(cfg)
    raise ValueError(name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--collector', default='mock')
    ap.add_argument('--output', default=None)
    ap.add_argument('--frames', type=int, default=1000)
    ap.add_argument('--sleep', type=float, default=0.05)
    args = ap.parse_args()
    cfg = load_config(args.config)
    output_name = args.output or cfg.get('matrix', {}).get('output', 'console')
    posts = MockCollector().fetch()
    messages = build_messages(posts, cfg)
    out = make_output(output_name, cfg)
    print(f'output={output_name}, messages={len(messages)}')
    msg_index = 0
    for frame in range(args.frames):
        msg = messages[msg_index % len(messages)]
        out.show(msg)
        if frame % 30 == 29:
            msg_index += 1
        time.sleep(args.sleep)

if __name__ == '__main__':
    main()
