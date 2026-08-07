import queue
import yaml
from datetime import datetime, timedelta, date

from src.models import DisplayMessage


class TimetableScheduler:
    """
    timetable.yaml を読み込み、各アーティストの開始時刻の
    advance_minutes 分前になったら interrupt_queue へ DisplayMessage を積む。

    同時刻に複数エントリがある場合は1件ずつ順番にキューへ積む（案B）。
    """

    def __init__(self, timetable_path: str, interrupt_queue: queue.Queue, advance_minutes: int = 10):
        self.advance = timedelta(minutes=advance_minutes)
        self.interrupt_queue = interrupt_queue
        self.fired: set = set()
        self.entries = self._load(timetable_path)

    def _load(self, path: str) -> list:
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        entries = []
        for day in data.get('timetable', []):
            base = date.fromisoformat(day['date'])
            for e in day.get('entries', []):
                h, m = map(int, e['time'].split(':'))
                # 25:40 のような26時間表記に対応
                extra_days, h = divmod(h, 24)
                start_dt = datetime(base.year, base.month, base.day, h, m) + timedelta(days=extra_days)
                trigger_dt = start_dt - self.advance
                key = f"{day['date']}_{e['time']}_{e['stage']}_{e['artist']}"
                entries.append({
                    'key': key,
                    'start_dt': start_dt,
                    'trigger_dt': trigger_dt,
                    'stage': e['stage'],
                    'artist': e['artist'],
                })
        return entries

    def tick(self):
        """
        メインループから毎フレーム呼び出す。
        trigger_dt を過ぎた未発火エントリをキューへ積む。
        複数件あれば1件ずつ順番に積む。
        """
        now = datetime.now()
        for e in self.entries:
            if e['key'] in self.fired:
                continue
            if e['trigger_dt'] <= now < e['start_dt']:
                self.fired.add(e['key'])
                msg = DisplayMessage(
                    message_type='interrupt',
                    title=f"NEXT: {e['stage']}",
                    body=f"{e['artist']} まもなくスタート！",
                    priority=100,
                )
                self.interrupt_queue.put(msg)

    def next_entry(self):
        """Return the nearest upcoming timetable entry and remaining seconds.

        Returns:
            tuple[dict | None, int | None]: (entry, remaining_seconds)
        """
        now = datetime.now()
        upcoming = [e for e in self.entries if e['start_dt'] >= now]
        if not upcoming:
            return None, None

        nxt = min(upcoming, key=lambda e: e['start_dt'])
        remaining = int((nxt['start_dt'] - now).total_seconds())
        return nxt, max(0, remaining)
