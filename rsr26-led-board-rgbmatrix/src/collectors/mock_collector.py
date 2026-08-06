from datetime import datetime, timezone
from src.models import Post

class MockCollector:
    def fetch(self):
        now = datetime.now(timezone.utc).isoformat()
        texts = [
            '#RSR26 LED実機テスト表示中',
            '#RSR26 会場着いた！空気が最高すぎる',
            '#RSR26 雨が少し降ってきたのでカッパあると安心',
            '#RSR26 これは長文スクロールテストです。電車の発車案内板みたいに流れるか確認します'
        ]
        return [Post('mock', f'sample-{i:03}', now, f'user{i}', t) for i, t in enumerate(texts, 1)]
