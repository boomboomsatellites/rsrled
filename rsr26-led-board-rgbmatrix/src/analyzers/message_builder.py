from src.models import DisplayMessage

def build_messages(posts, cfg):
    title = cfg.get('message_builder', {}).get('title_text', '#RSR26 LIVE')
    prefix = cfg.get('message_builder', {}).get('latest_post_prefix', '>')
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
        # posted_at を渡す
        msgs.append(DisplayMessage(
            'latest_post', 
            combined, 
            f'{prefix} {p.text}',
            posted_at=p.posted_at  # ← 追加
        ))
    
    msgs.append(DisplayMessage('summary', 'RSR26 NOW', '投稿を受信中'))
    return msgs