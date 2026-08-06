from src.models import DisplayMessage

def build_messages(posts, cfg):
    title = cfg.get('message_builder', {}).get('title_text', '#RSR26 LIVE')
    msgs = [DisplayMessage('title', title, 'NOW STREAMING')]
    for p in posts:
        msgs.append(DisplayMessage('latest_post', 'LATEST', p.text))
    msgs.append(DisplayMessage('summary', 'RSR26 NOW', '投稿を受信中'))
    return msgs
