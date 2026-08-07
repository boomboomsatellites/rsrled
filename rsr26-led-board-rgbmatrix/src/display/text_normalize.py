from __future__ import annotations

try:
    import emoji
except Exception:
    emoji = None


def _demojize_token(token: str) -> str:
    out = emoji.demojize(token, delimiters=(' ', ' '))
    out = out.replace('_', ' ')
    out = ' '.join(out.split())
    return out


def normalize_display_text(text: str, cfg, can_render_emoji=None) -> str:
    if text is None:
        return ''
    out = str(text)

    display_cfg = cfg.get('display', {})
    if not bool(display_cfg.get('emoji_demojize', True)) or emoji is None:
        return out

    mode = str(display_cfg.get('emoji_demojize_mode', 'missing_only')).lower()
    if mode == 'all' or can_render_emoji is None:
        return _demojize_token(out)

    items = emoji.emoji_list(out)
    if not items:
        return out

    parts = []
    cursor = 0
    for item in items:
        start = item['match_start']
        end = item['match_end']
        em = item['emoji']
        if start > cursor:
            parts.append(out[cursor:start])
        if can_render_emoji(em):
            parts.append(em)
        else:
            parts.append(_demojize_token(em))
        cursor = end
    if cursor < len(out):
        parts.append(out[cursor:])

    return ''.join(parts)
