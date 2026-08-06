import asyncio
import logging
from datetime import datetime, timezone

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
    """

    def __init__(self, cfg):
        app_cfg = cfg.get('app', {})
        collector_cfg = cfg.get('collector', {})
        self.hashtag = app_cfg.get('hashtag', '#RSR26')
        self.max_results = int(collector_cfg.get('max_results', 20))
        self.exclude_retweets = bool(collector_cfg.get('exclude_retweets', True))
        self.db_path = collector_cfg.get('db_path', 'accounts.db')
        self._api = None
        self.since_id = None

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

        posts = []
        for tweet in raw:
            posted_at = tweet.date.isoformat() if getattr(tweet, 'date', None) else datetime.now(timezone.utc).isoformat()
            username = tweet.user.username if getattr(tweet, 'user', None) else 'unknown'
            posts.append(Post(
                source='x',
                external_id=str(tweet.id),
                posted_at=posted_at,
                author_name=username,
                text=getattr(tweet, 'rawContent', '') or '',
                url=getattr(tweet, 'url', '') or '',
            ))
        return posts
