from __future__ import annotations

import random
import time
from pathlib import Path

import imageio.v2 as imageio
from PIL import Image, ImageOps


class IdleMediaPlayer:
    def __init__(self, cfg):
        self.cfg = cfg
        matrix = cfg.get('matrix', {})
        media_cfg = cfg.get('idle_media', {})

        self.width = int(matrix.get('width', 128))
        self.height = int(matrix.get('height', 64))
        self.enabled = bool(media_cfg.get('enabled', False))
        self.folder = Path(media_cfg.get('folder', 'idle_media'))
        self.image_seconds = float(media_cfg.get('image_seconds', 5.0))
        self.video_fps_cap = float(media_cfg.get('video_fps_cap', 12.0))
        self.scan_interval_seconds = float(media_cfg.get('scan_interval_seconds', 5.0))
        self.random_mode = bool(media_cfg.get('random', False))

        self._image_ext = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
        self._video_ext = {'.mp4', '.mov', '.avi', '.mkv', '.gif'}

        self._last_scan = 0.0
        self._files = []
        self._index = -1

        self._current_path = None
        self._current_kind = None
        self._current_image = None
        self._switch_at = 0.0

        self._video_reader = None
        self._video_frame_interval = 1.0 / max(1.0, self.video_fps_cap)
        self._video_next_at = 0.0
        self._video_last_frame = None

    def _fit(self, img: Image.Image) -> Image.Image:
        img = img.convert('RGB')
        return ImageOps.fit(img, (self.width, self.height), method=Image.Resampling.LANCZOS)

    def _scan_files(self):
        now = time.monotonic()
        if now - self._last_scan < self.scan_interval_seconds:
            return
        self._last_scan = now

        if not self.folder.exists() or not self.folder.is_dir():
            self._files = []
            return

        files = []
        for p in self.folder.iterdir():
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext in self._image_ext or ext in self._video_ext:
                files.append(p)

        if self.random_mode:
            random.shuffle(files)
        else:
            files.sort()

        old = [str(x) for x in self._files]
        new = [str(x) for x in files]
        if old != new:
            self._files = files
            self._index = -1
            self._close_video()
            self._current_path = None
            self._current_kind = None
            self._current_image = None

    def _close_video(self):
        if self._video_reader is not None:
            try:
                self._video_reader.close()
            except Exception:
                pass
        self._video_reader = None
        self._video_last_frame = None

    def _next_path(self):
        if not self._files:
            return None
        self._index = (self._index + 1) % len(self._files)
        return self._files[self._index]

    def _start_item(self, path: Path):
        self._close_video()
        self._current_path = path
        ext = path.suffix.lower()
        now = time.monotonic()

        if ext in self._image_ext:
            self._current_kind = 'image'
            with Image.open(path) as img:
                self._current_image = self._fit(img)
            self._switch_at = now + max(0.5, self.image_seconds)
            return

        self._current_kind = 'video'
        self._video_reader = imageio.get_reader(str(path))
        meta = {}
        try:
            meta = self._video_reader.get_meta_data() or {}
        except Exception:
            meta = {}

        fps = float(meta.get('fps') or self.video_fps_cap)
        fps = max(1.0, min(fps, self.video_fps_cap))
        self._video_frame_interval = 1.0 / fps
        self._video_next_at = now

    def next_frame(self):
        if not self.enabled:
            return None, 0.2

        self._scan_files()
        if not self._files:
            return None, 0.5

        if self._current_path is None:
            path = self._next_path()
            if path is None:
                return None, 0.5
            try:
                self._start_item(path)
            except Exception:
                self._current_path = None
                return None, 0.2

        now = time.monotonic()
        if self._current_kind == 'image':
            if now >= self._switch_at:
                path = self._next_path()
                if path is not None:
                    try:
                        self._start_item(path)
                    except Exception:
                        self._current_path = None
                        return None, 0.2
            return self._current_image, 0.1

        if self._current_kind == 'video':
            if now < self._video_next_at and self._video_last_frame is not None:
                return self._video_last_frame, 0.02

            try:
                frame = self._video_reader.get_next_data()
                img = Image.fromarray(frame)
                img = self._fit(img)
                self._video_last_frame = img
                self._video_next_at = now + self._video_frame_interval
                return img, max(0.01, self._video_frame_interval)
            except Exception:
                path = self._next_path()
                self._current_path = None
                if path is not None:
                    try:
                        self._start_item(path)
                    except Exception:
                        return None, 0.2
                return None, 0.05

        return None, 0.2
