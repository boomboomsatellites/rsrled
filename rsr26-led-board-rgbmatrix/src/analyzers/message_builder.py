from src.models import DisplayMessage

def build_messages(posts, cfg):
    title = cfg.get('message_builder', {}).get('title_text', '#RSR26 LIVE')
    prefix = cfg.get('message_builder', {}).get('latest_post_prefix', '>')
    msgs = [DisplayMessage('title', title, 'NOW STREAMING')]
    for p in posts:
        msgs.append(DisplayMessage('latest_post', 'LATEST', f'{prefix} {p.text}'))
    msgs.append(DisplayMessage('summary', 'RSR26 NOW', '投稿を受信中'))
    return msgs
