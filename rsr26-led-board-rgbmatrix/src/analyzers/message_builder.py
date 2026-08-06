from src.models import DisplayMessage

def build_messages(posts, cfg):
    title = cfg.get('message_builder', {}).get('title_text', '#RSR26 LIVE')
    prefix = cfg.get('message_builder', {}).get('latest_post_prefix', '>')
    msgs = [DisplayMessage('title', title, 'NOW STREAMING')]
    
    for p in posts:
        handle = getattr(p, 'author_name', None) or getattr(p, 'username', None) or 'UNKNOWN'
        display = getattr(p, 'display_name', '') or ''
        
        # 組み合わせパターン
        if display and display != handle:
            # 表示名とハンドル名が異なる場合
            # 優先順位：表示名 > ハンドル名 > 両方
            combined = f"{display} (@{handle})"
            if len(combined) > 20:
                # 20文字を超えるなら表示名優先、それでも長ければハンドル名のみ
                combined = display[:20] if len(display) <= 20 else f"@{handle}"
        else:
            # 表示名がない、または同じ場合はハンドル名のみ
            combined = f"@{handle}"
        
        combined = combined[:20]
        msgs.append(DisplayMessage('latest_post', combined, f'{prefix} {p.text}'))
    
    msgs.append(DisplayMessage('summary', 'RSR26 NOW', '投稿を受信中'))
    return msgs