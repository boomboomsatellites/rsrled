from __future__ import annotations

import threading
from queue import Queue, Empty

from flask import Flask, jsonify, redirect, render_template_string, request

from src.models import DisplayMessage


class RemoteControlState:
    def __init__(self):
        self._mode = 'auto'
        self._lock = threading.Lock()
        self._messages = Queue()

    def set_mode(self, mode: str):
        allowed = {'auto', 'text_only', 'media_only', 'pause'}
        if mode not in allowed:
            raise ValueError(f'invalid mode: {mode}')
        with self._lock:
            self._mode = mode

    def get_mode(self) -> str:
        with self._lock:
            return self._mode

    def enqueue_message(self, title: str, body: str):
        title = (title or 'MANUAL')[:20]
        body = (body or '').strip()
        if not body:
            return
        self._messages.put(DisplayMessage(message_type='manual', title=title, body=body, priority=90))

    def pop_message(self):
        try:
            return self._messages.get_nowait()
        except Empty:
            return None

    def snapshot(self):
        return {
            'mode': self.get_mode(),
            'pending_manual_messages': self._messages.qsize(),
        }


def start_web_control(cfg, state: RemoteControlState):
    rcfg = cfg.get('remote_control', {})
    if not bool(rcfg.get('enabled', False)):
        return None

    host = str(rcfg.get('host', '0.0.0.0'))
    port = int(rcfg.get('port', 5000))
    token = str(rcfg.get('token', '')).strip()

    app = Flask(__name__)

    def _authorized(req):
        if not token:
            return True

        sent = req.headers.get('X-Token', '')
        if sent == token:
            return True

        auth = req.headers.get('Authorization', '')
        if auth.startswith('Bearer ') and auth[7:] == token:
            return True

        req_token = req.values.get('token', '')
        return req_token == token

    @app.before_request
    def _guard():
        if request.path == '/health':
            return None
        if not _authorized(request):
            return jsonify({'error': 'unauthorized'}), 401
        return None

    @app.get('/health')
    def health():
        return jsonify({'ok': True})

    @app.get('/api/state')
    def api_state():
        return jsonify(state.snapshot())

    @app.post('/api/mode')
    def api_mode():
        payload = request.get_json(silent=True) or request.form
        mode = str(payload.get('mode', 'auto'))
        state.set_mode(mode)
        return jsonify({'ok': True, 'mode': state.get_mode()})

    @app.post('/api/message')
    def api_message():
        payload = request.get_json(silent=True) or request.form
        title = str(payload.get('title', 'MANUAL'))
        body = str(payload.get('body', ''))
        state.enqueue_message(title, body)
        return jsonify({'ok': True})

    @app.get('/')
    def index():
        snap = state.snapshot()
        html = """
<!doctype html>
<html>
<head>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>RSR26 LED Controller</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }
    h1 { font-size: 20px; margin-bottom: 8px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin-bottom: 12px; }
    button { font-size: 16px; padding: 10px 14px; margin: 4px; }
    input, textarea, select { width: 100%; font-size: 16px; padding: 8px; box-sizing: border-box; }
    textarea { min-height: 88px; }
  </style>
</head>
<body>
  <h1>RSR26 LED Controller</h1>
  <div>Mode: <b>{{ mode }}</b> / Pending: {{ pending }}</div>

  <div class=\"card\">
    <form method=\"post\" action=\"/api/mode\">
      <input type=\"hidden\" name=\"token\" value=\"{{ token }}\" />
      <label>Mode</label>
      <select name=\"mode\">
        <option value=\"auto\">auto</option>
        <option value=\"text_only\">text_only</option>
        <option value=\"media_only\">media_only</option>
        <option value=\"pause\">pause</option>
      </select>
      <button type=\"submit\">Set mode</button>
    </form>
  </div>

  <div class=\"card\">
    <form method=\"post\" action=\"/api/message\">
      <input type=\"hidden\" name=\"token\" value=\"{{ token }}\" />
      <label>Title</label>
      <input name=\"title\" value=\"MANUAL\" maxlength=\"20\" />
      <label>Body</label>
      <textarea name=\"body\" placeholder=\"表示したい文言\"></textarea>
      <button type=\"submit\">Queue message</button>
    </form>
  </div>
</body>
</html>
        """
        return render_template_string(
            html,
            mode=snap['mode'],
            pending=snap['pending_manual_messages'],
            token=token,
        )

    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return thread
