import argparse, time, threading, queue, os
from src.models import DisplayMessage
from src.config import load_config
from src.collectors.factory import create_collector
from src.analyzers.message_builder import build_messages
from src.outputs.console_output import ConsoleOutput
from src.outputs.preview_output import PreviewOutput
from src.outputs.rgb_matrix_output import RGBMatrixOutput
from src.scheduler.timetable_scheduler import TimetableScheduler


def make_output(name, cfg):
    if name == 'console': return ConsoleOutput(cfg)
    if name == 'preview': return PreviewOutput(cfg)
    if name == 'rgb_matrix': return RGBMatrixOutput(cfg)
    raise ValueError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--output', default=None)
    ap.add_argument('--frames', type=int, default=None)
    ap.add_argument('--sleep', type=float, default=0.01)
    ap.add_argument('--timetable', default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    output_name = args.output or cfg.get('matrix', {}).get('output', 'console')
    collector_cfg = cfg.get('collector', {})
    poll_interval = float(collector_cfg.get('poll_interval_seconds', 30))
    max_buffer = int(collector_cfg.get('max_buffer', 20))

    collector = create_collector(cfg)
    out = make_output(output_name, cfg)

    # タイムテーブルスケジューラ初期化
    interrupt_queue = queue.Queue()
    scheduler_cfg = cfg.get('scheduler', {})
    timetable_path = args.timetable or scheduler_cfg.get('timetable_path', 'timetable.yaml')
    advance_minutes = int(scheduler_cfg.get('advance_minutes', 10))
    countdown_enabled = bool(scheduler_cfg.get('countdown_enabled', True))
    countdown_refresh_seconds = float(scheduler_cfg.get('countdown_refresh_seconds', 1.0))
    if os.path.exists(timetable_path):
        scheduler = TimetableScheduler(timetable_path, interrupt_queue, advance_minutes)
        print(f"timetable loaded: {timetable_path} (advance={advance_minutes}min)")
    else:
        scheduler = None
        print(f"timetable not found: {timetable_path}, scheduler disabled")

    posts = []
    seen_ids = set()
    print(f"output={output_name}, collector={collector_cfg.get('type', 'mock')}")

    pending = []
    current = None
    done = True
    last_countdown = 0.0

    # フェッチ結果を受け取るキュー
    fetch_queue = queue.Queue()
    stop_event = threading.Event()

    def fetch_worker():
        """別スレッドで定期fetch。メインループをブロックしない"""
        last_fetch = 0.0
        while not stop_event.is_set():
            now = time.monotonic()
            if now - last_fetch >= poll_interval:
                last_fetch = now
                try:
                    new_posts = collector.fetch()
                    fetch_queue.put(new_posts)
                except Exception as e:
                    print(f'collector fetch error: {e}')
                    fetch_queue.put([])
            time.sleep(1)

    # フェッチ用スレッド開始
    fetch_thread = threading.Thread(target=fetch_worker, daemon=True)
    fetch_thread.start()

    try:
        while True:
            # タイムテーブル割り込みチェック
            if scheduler:
                scheduler.tick()

            # ノンブロッキングでキューから新着を取得
            while True:
                try:
                    new_posts = fetch_queue.get_nowait()
                    fresh = [p for p in new_posts if p.external_id not in seen_ids]
                    if fresh:
                        for p in fresh:
                            seen_ids.add(p.external_id)
                        posts.extend(fresh)
                        posts = posts[-max_buffer:]
                        seen_ids = {p.external_id for p in posts}
                        new_msgs = build_messages(fresh, cfg)
                        for m in new_msgs:
                            if m.message_type == 'latest_post':
                                pending.append(m)
                        print(f'new posts: {len(fresh)}, pending: {len(pending)}')
                except queue.Empty:
                    break

            if done:
                # 割り込みキューを通常キューより優先して取り出す
                try:
                    current = interrupt_queue.get_nowait()
                    print(f'[INTERRUPT] {current.title}: {current.body}')
                except queue.Empty:
                    if pending:
                        current = pending.pop(0)
                        print(f'display: {current.title}')
                    else:
                        current = None

            if current:
                done = out.show(current)
            else:
                if scheduler and countdown_enabled:
                    now = time.monotonic()
                    if now - last_countdown >= max(0.2, countdown_refresh_seconds):
                        entry, remain = scheduler.next_entry()
                        if entry and remain is not None:
                            mm, ss = divmod(remain, 60)
                            hh, mm = divmod(mm, 60)
                            if hh > 0:
                                remain_text = f"{hh:02d}:{mm:02d}:{ss:02d}"
                            else:
                                remain_text = f"{mm:02d}:{ss:02d}"
                            countdown_msg = DisplayMessage(
                                message_type='countdown',
                                title=f"NEXT: {entry['stage']}",
                                body=f"{entry['artist']} まで {remain_text}",
                            )
                            out.show(countdown_msg)
                        last_countdown = now
                time.sleep(0.1)
                continue

            time.sleep(args.sleep)

    except KeyboardInterrupt:
        stop_event.set()
        fetch_thread.join(timeout=2)
        print("\nStopped by user.")


if __name__ == '__main__':
    main()