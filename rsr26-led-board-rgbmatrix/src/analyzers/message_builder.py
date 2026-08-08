import re

from src.models import DisplayMessage

_URL_PATTERN = re.compile(r'https?://\S+')


def _strip_urls(text: str) -> str:
    """本文からURL（画像/動画リンクを含む）を除去し、余分な空白を整える。"""
    if not text:
        return text
    cleaned = _URL_PATTERN.sub('', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def build_messages(posts, cfg):
    title = cfg.get('message_builder', {}).get('title_text', '#RSR26 LIVE')
    prefix = cfg.get('message_builder', {}).get('latest_post_prefix', '>')
    remove_urls = bool(cfg.get('filters', {}).get('remove_urls', True))
    msgs = [DisplayMessage('title', title, 'NOW STREAMING')]
    
    for p in posts:
        handle = getattr(p, 'author_name', None) or getattr(p, 'username', None) or 'UNKNOWN'
        display = getattr(p, 'display_name', '') or ''
        
        if display and display != handle:
            combined = f"{display} (@{handle})"
            if len(combined) > 20:
                combined = display[:20] if len(display) <= 20 else f"@{handle}"
        else:
            combined = f"@{handle}" if not str(handle).startswith('@') else str(handle)
        
        combined = combined[:20]

        text = p.text
        if remove_urls:
            text = _strip_urls(text)

        # posted_at を渡す
        msgs.append(DisplayMessage(
            'latest_post', 
            combined, 
            f'{prefix} {text}',
            posted_at=p.posted_at  # ← 追加
        ))
    
    msgs.append(DisplayMessage('summary', 'RSR26 NOW', '投稿を受信中'))
    return msgs