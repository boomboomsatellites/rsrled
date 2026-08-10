import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.models import Post

logger = logging.getLogger(__name__)


class TwscrapeCollector:
    """Fetches recent posts matching a hashtag via twscrape (unofficial X scraper).

    Notes:
    - Requires an accounts DB set up beforehand with the twscrape CLI:
        twscrape add_accounts accounts.txt username:password:email:email_password
        twscrape login_accounts
      This creates accounts.db in the working directory. Point db_path at it
      (or copy it next to where this process runs).
    - twscrape talks to X's internal GraphQL endpoints using logged-in account
      sessions. It is NOT the official API and can break when X changes its
      backend, and it goes against X's Terms of Service. Treat it as
      best-effort: keep a fallback collector ready in case it stops working.
    - Only new posts (id greater than the last seen id) are returned on each
      call, so repeated polling does not re-emit the same posts.
    - The last-seen id is persisted to disk (state_path) so that restarting
      the process does not re-fetch/re-display already-seen posts.
    """

    def __init__(self, cfg):
        app_cfg = cfg.get('app', {})
        collector_cfg = cfg.get('collector', {})
        self.hashtag = app_cfg.get('hashtag', '#RSR26')
        self.max_results = int(collector_cfg.get('max_results', 20))
        self.exclude_retweets = bool(collector_cfg.get('exclude_retweets', True))
        self.db_path = collector_cfg.get('db_path', 'accounts.db')
        self.state_path = Path(collector_cfg.get('state_path', 'twscrape_state.json'))
        self._api = None
        self.since_id = self._load_since_id()

    def _load_since_id(self):
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text(encoding='utf-8'))
                since_id = data.get('since_id')
                if since_id is not None:
                    logger.info(f'twscrape: resuming from since_id={since_id}')
                    return int(since_id)
        except Exception:
            logger.exception('twscrape: failed to load state; starting fresh')
        return None

    def _save_since_id(self):
        try:
            self.state_path.write_text(
                json.dumps({'since_id': self.since_id}),
                encoding='utf-8',
            )
        except Exception:
            logger.exception('twscrape: failed to persist state')

    def set_hashtag(self, hashtag: str):
        """UI等からハッシュタグを切り替える。切り替え時は since_id をリセットし、
        新しいハッシュタグで最初から(max_results件まで)取得し直す。"""
        hashtag = (hashtag or '').strip()
        if not hashtag:
            return
        if hashtag == self.hashtag:
            return
        logger.info(f'twscrape: hashtag changed {self.hashtag} -> {hashtag}')
        self.hashtag = hashtag
        self.since_id = None
        self._save_since_id()

    def _get_api(self):
        if self._api is None:
            from twscrape import API
            self._api = API(self.db_path)
        return self._api

    def _build_query(self):
        query = self.hashtag
        if self.exclude_retweets:
            query += ' -filter:retweets'
        return query

    def fetch(self):
        try:
            return asyncio.run(self._fetch_async())
        except Exception:
            logger.exception('twscrape fetch failed; returning no new posts')
            return []

    async def _fetch_async(self):
        api = self._get_api()
        query = self._build_query()
        raw = []
        async for tweet in api.search(query, limit=self.max_results):
            if self.since_id is not None and tweet.id <= self.since_id:
                break
            raw.append(tweet)

        if not raw:
            return []

        raw.sort(key=lambda t: t.id)
        self.since_id = raw[-1].id
        self._save_since_id()

        posts = []
        for tweet in raw:
            posted_at = tweet.date.isoformat() if getattr(tweet, 'date', None) else datetime.now(timezone.utc).isoformat()
            username = tweet.user.username if getattr(tweet, 'user', None) else 'unknown'
            posts.append(Post(
                source='x',
                external_id=str(tweet.id),
                posted_at=posted_at,
                author_name=username,
                display_name=tweet.user.displayname if getattr(tweet, 'user', None) else '',
                text=getattr(tweet, 'rawContent', '') or '',
                url=getattr(tweet, 'url', '') or '',
            ))
        return posts
