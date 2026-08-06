import argparse, time
from src.config import load_config
from src.collectors.factory import create_collector
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
    ap.add_argument('--output', default=None)
    ap.add_argument('--frames', type=int, default=1000)
    ap.add_argument('--sleep', type=float, default=0.05)
    args = ap.parse_args()
    cfg = load_config(args.config)
    output_name = args.output or cfg.get('matrix', {}).get('output', 'console')
    collector_cfg = cfg.get('collector', {})
    poll_interval = float(collector_cfg.get('poll_interval_seconds', 30))
    max_buffer = int(collector_cfg.get('max_buffer', 20))

    collector = create_collector(cfg)
    out = make_output(output_name, cfg)

    posts = []
    seen_ids = set()
    messages = build_messages(posts, cfg)
    print(f"output={output_name}, collector={collector_cfg.get('type', 'mock')}, messages={len(messages)}")

    index = 0
    last_fetch = 0.0
    for _ in range(args.frames):
        now = time.monotonic()
        if now - last_fetch >= poll_interval:
            last_fetch = now
            try:
                new_posts = collector.fetch()
            except Exception as e:
                print(f'collector fetch error: {e}')
                new_posts = []
            fresh = [p for p in new_posts if p.external_id not in seen_ids]
            if fresh:
                for p in fresh:
                    seen_ids.add(p.external_id)
                posts.extend(fresh)
                posts = posts[-max_buffer:]
                seen_ids = {p.external_id for p in posts}
                messages = build_messages(posts, cfg)
                print(f'new posts: {len(fresh)}, total buffered: {len(posts)}')

        msg = messages[index % len(messages)]
        done = out.show(msg)
        if done:
            index += 1
        time.sleep(args.sleep)

if __name__ == '__main__':
    main()
