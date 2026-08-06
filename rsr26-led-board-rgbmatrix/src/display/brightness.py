from datetime import time

def _parse(v):
    h, m = v.split(':')
    return time(int(h), int(m))

def is_night(current, start, end):
    s, e = _parse(start), _parse(end)
    return s <= current < e if s <= e else current >= s or current < e

def select_brightness(cfg, current):
    m = cfg.get('matrix', {})
    if is_night(current, m.get('night_start', '18:00'), m.get('night_end', '05:00')):
        return int(m.get('brightness_night', m.get('brightness', 60)))
    return int(m.get('brightness_day', m.get('brightness', 60)))
