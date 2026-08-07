# RSR26 LED Board - 実装設計書 (引き継ぎ用)

この文書は、現時点で実装済みの機能を他のAI/開発者へ引き継ぐための設計書です。
対象リポジトリ: `rsr26-led-board-rgbmatrix`

## 1. 目的

本システムは、X投稿や運営メッセージをLEDマトリクスへ表示するランタイムです。
現時点で、以下の機能を実装済みです。

- 投稿取得/表示ローテーション
- タイムテーブル割り込み表示
- 投稿待機時のメディア再生 (画像/動画)
- 待機メディアへの時刻オーバーレイ
- 絵文字の条件付きフォールバック表示
- iPhone (Web UI) からのモード切替/手動メッセージ投入

## 2. 全体アーキテクチャ

主要モジュール:

- `src/main.py`: 全体オーケストレーション
- `src/collectors/*`: 投稿収集 (mock / twscrape)
- `src/analyzers/message_builder.py`: Post -> DisplayMessage 変換
- `src/outputs/*`: 出力先ごとの表示実装
- `src/scheduler/timetable_scheduler.py`: 割り込みスケジューラ
- `src/display/idle_media.py`: 待機メディア再生 + 時計描画
- `src/display/textdraw.py`: フォントフォールバック描画/幅計測
- `src/display/text_normalize.py`: 絵文字テキスト正規化
- `src/control/web_control.py`: Flask制御UI/API

### 2.1 スレッド構成

- Main thread:
  - メッセージ選択・描画・モード判定
- Fetch thread:
  - collector を定期実行し、fetch_queue に新着を投入
- Flask thread:
  - Web UI/API 提供 (`remote_control.enabled=true` のとき)

## 3. メインループ設計

`src/main.py` の優先順位は以下:

1. タイムテーブル割り込み (`interrupt_queue`)
2. 手動メッセージ (`RemoteControlState.pop_message()`)
3. 通常投稿 (`pending`)
4. 待機中表示
   - mode=auto/media_only: 待機メディア
   - mode=auto/text_only: カウントダウン表示

`mode=pause` の場合:

- 投稿/メディア/カウントダウンは表示しない
- 割り込みと手動メッセージは表示対象

## 4. データモデル

`src/models.py`

- `Post`
  - `source`, `external_id`, `posted_at`, `author_name`, `text`, `url`, `display_name`
- `DisplayMessage`
  - `message_type`, `title`, `body`, `priority`, `duration_seconds`, `posted_at`

## 5. 機能詳細

### 5.1 投稿取得と重複排除

- fetch thread で `collector.fetch()` を実行
- `external_id` を `seen_ids` で管理し重複排除
- `max_buffer` 超過時は古い投稿を破棄

対象:

- `src/main.py`
- `src/collectors/factory.py`
- `src/collectors/twscrape_collector.py`

### 5.2 タイムテーブル割り込み & カウントダウン

割り込み:

- `TimetableScheduler.tick()` が trigger 時間帯で `interrupt` メッセージを enqueue

カウントダウン:

- `TimetableScheduler.next_entry()` が次の開始予定と残秒を返却
- 投稿待機時に `NEXT: <stage>` / `<artist> まで MM:SS` を表示

対象:

- `src/scheduler/timetable_scheduler.py`
- `src/main.py`

### 5.3 待機メディア再生

`IdleMediaPlayer` の責務:

- フォルダ走査 (`scan_interval_seconds`)
- 対応拡張子判定
  - image: png/jpg/jpeg/bmp/webp
  - video: mp4/mov/avi/mkv/gif
- 画像: `image_seconds` ごと切替
- 動画: `imageio` reader でフレーム取得、`video_fps_cap` で上限
- LED解像度へ `ImageOps.fit`

対象:

- `src/display/idle_media.py`
- `src/main.py`
- `src/outputs/rgb_matrix_output.py` (`show_image`)
- `src/outputs/preview_output.py` (`show_image`)
- `src/outputs/console_output.py` (`show_image`)

### 5.4 待機メディア時刻オーバーレイ

`IdleMediaPlayer._apply_clock_overlay()`:

- 現在時刻を `clock_format` で描画
- 位置: top_left/top_right/bottom_left/bottom_right
- スタイル: `clock_color`, `clock_shadow`, `clock_font_size`, margin

対象:

- `src/display/idle_media.py`

### 5.5 絵文字の条件付きフォールバック

要件:

- まず絵文字フォント描画を試す
- 描けない絵文字だけテキスト化

実装:

- `textdraw.py`
  - `load_fonts`: font_candidates の複数ロード
  - `font_supports_text`: glyph signature 判定
  - `_iter_tokens`: emoji を1トークン単位で分解
  - `draw_text_bold`: トークンごと最適フォントで描画
  - `measure_text_width`: 同ロジックで幅計測
- `text_normalize.py`
  - `normalize_display_text(..., can_render_emoji=...)`
  - mode=`missing_only` 時は、描けない絵文字のみ demojize

対象:

- `src/display/textdraw.py`
- `src/display/text_normalize.py`
- `src/outputs/rgb_matrix_output.py`

### 5.6 iPhone制御 (Flask)

`RemoteControlState`:

- mode 管理 (`auto`, `text_only`, `media_only`, `pause`)
- 手動メッセージキュー管理

HTTP API:

- `GET /health` (認証不要)
- `GET /api/state`
- `POST /api/mode` `{mode}`
- `POST /api/message` `{title, body}`
- `GET /` (簡易HTML UI)

認証:

- token が空でなければ必須
- 受け付け手段:
  - `X-Token` ヘッダ
  - `Authorization: Bearer <token>`
  - フォーム/クエリ `token`

対象:

- `src/control/web_control.py`
- `src/main.py`

## 6. 主要設定 (`config.yaml`)

### 6.1 待機メディア

```yaml
idle_media:
  enabled: true
  folder: "idle_media"
  image_seconds: 5
  video_fps_cap: 12
  random: false
  scan_interval_seconds: 5
  clock_overlay_enabled: true
  clock_format: "%H:%M:%S"
  clock_position: "bottom_right"
  clock_margin_x: 2
  clock_margin_y: 2
  clock_font_size: 8
  clock_color: [220, 220, 220]
  clock_shadow: true
```

### 6.2 絵文字

```yaml
display:
  emoji_demojize: true
  emoji_demojize_mode: "missing_only"  # missing_only or all
```

### 6.3 リモート制御

```yaml
remote_control:
  enabled: true
  host: "0.0.0.0"
  port: 5000
  token: "change-me"
```

### 6.4 カウントダウン

```yaml
scheduler:
  timetable_path: "timetable.yaml"
  advance_minutes: 10
  countdown_enabled: true
  countdown_refresh_seconds: 1.0
```

## 7. 出力バックエンドの差分

- `RGBMatrixOutput`
  - メッセージ描画 + 画像フレーム表示 (`show_image`)
- `PreviewOutput`
  - `preview_frame.png` 出力でプレビュー
- `ConsoleOutput`
  - テキストボックス表示、画像時はログ出力

## 8. 依存関係

`requirements.txt` で追加済み:

- Flask
- imageio
- imageio-ffmpeg
- emoji

既存:

- PyYAML
- Pillow
- pytest
- twscrape

## 9. 既知課題 / 注意点

1. `src/main.py` の `--frames` 引数は現在未使用。
2. `src/control/web_control.py` の `redirect` import は未使用。
3. `pause` モードでも割り込み/手動メッセージは表示される仕様。
4. 絵文字描画品質はフォント依存。環境により `NotoColorEmoji.ttf` / `Symbola` の実体パスが異なる。
5. `IdleMediaPlayer` はフォルダ全件再走査方式。素材数が多い場合はI/O最適化余地あり。

## 10. 引き継ぎ時の実装優先候補

1. Web UI プリセットボタン化 (`/api/preset` 追加)
2. pause モード仕様の明確化 (割り込み許可の是非)
3. `--frames` 実装 or 引数削除
4. Web control の簡易監査ログ (誰が何を送信したか)
5. フォント存在チェックを起動時に警告表示

## 11. 変更時の安全ガイド

- 描画ロジック変更時は、以下を同時に整合させること:
  - `text_width`
  - `draw_text_bold`
  - body/title キャッシュキー
- `IdleMediaPlayer.next_frame()` は `(PIL.Image|None, wait_seconds)` 契約を維持すること。
- Web API 追加時は `before_request` 認証ルールに従うこと。

## 12. クイック起動手順

```bash
pip install -r requirements.txt
python3 -m src.main --config config.yaml --output preview
```

実機:

```bash
sudo -E python3 -m src.main --config config.yaml --output rgb_matrix
```

---

必要なら次版で、上記をPlantUMLや詳細シーケンス図付きの「運用設計書」と「API仕様書」に分割可能です。
