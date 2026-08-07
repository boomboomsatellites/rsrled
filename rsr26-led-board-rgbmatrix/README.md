# RSR26 LED Matrix Live Board: scroll-complete版

本文スクロールが途中で次画面に切り替わらないよう、**スクロールが最後まで流れてから次メッセージへ進む** 実装に変更した版です。

## 実機表示

```bash
pip install -r requirements.txt
sudo -E python3 -m src.main --output rgb_matrix --frames 1000 --sleep 0.05
```

または:

```bash
./scripts/run_rgb_matrix.sh
```

## スクロール関連設定

```yaml
scroll:
  step_pixels: 2
  end_hold_frames: 20
  short_message_frames: 60
```

- `step_pixels`: スクロール速度。小さいほどゆっくり。
- `end_hold_frames`: 最後まで流れた後の待ち時間。
- `short_message_frames`: スクロール不要な短文の表示フレーム数。

## 待機中メディア表示（画像 / 動画）

投稿待ちの間は、指定フォルダの素材を自動再生できます。

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

- `folder` に配置した `png/jpg/webp/mp4/gif` などを再生します。
- 新しい投稿が来たら投稿表示が優先されます。
- `clock_overlay_enabled: true` で待機メディア上に現在時刻を重ねます。

## 絵文字の豆腐化対策

低解像度LEDとフォント制約で絵文字が豆腐化しやすいため、表示直前に
絵文字を短いテキストへ展開できます（例: 😀 → grinning face）。

```yaml
display:
  emoji_demojize: true
  emoji_demojize_mode: "missing_only" # "missing_only" or "all"
```

加えて、フォント候補に絵文字フォントを追加すると表示品質が上がります。

Ubuntu (Raspberry Pi OS / Ubuntu系) での導入例:

```bash
sudo apt update
sudo apt install -y fonts-noto-color-emoji fonts-symbola
fc-cache -f -v
```

環境によって `fonts-symbola` が見つからない場合は、次を試してください。

```bash
sudo apt install -y ttf-ancient-fonts
fc-cache -f -v
```

インストール確認:

```bash
fc-list | grep -E "NotoColorEmoji|Symbola"
```

`config.yaml` の `rgb_matrix.font_candidates` には以下を指定します。

```yaml
rgb_matrix:
  font_candidates:
    - "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    - "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
    - "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf"
```

- `missing_only`: 描ける絵文字はそのまま表示し、描けない絵文字だけテキスト化
- `all`: 従来通り、絵文字をすべてテキスト化

## iPhoneから文言・モード切替（Flask）

同一LAN内のiPhone Safariから、表示モード切替と手動メッセージ投入ができます。

```yaml
remote_control:
  enabled: true
  host: "0.0.0.0"
  port: 5000
  token: "change-me"
```

起動後に `http://<RaspberryPiのIP>:5000` へアクセスしてください。

- mode: `auto` / `text_only` / `media_only` / `pause`
- manual message: タイトルと本文をキュー投入

`token` は必ず変更してください。空文字にすると認証なしで公開されます。

## 次の予定カウントダウン表示

投稿待機中（新しい投稿が来るまでの間）は、タイムテーブルから次の予定を取得して
`NEXT: ステージ名` / `出演者 まで MM:SS` を表示できます。

```yaml
scheduler:
  timetable_path: "timetable.yaml"
  advance_minutes: 10
  countdown_enabled: true
  countdown_refresh_seconds: 1.0
```

- `countdown_enabled`: `true` で待機中にカウントダウンを表示
- `countdown_refresh_seconds`: 表示更新間隔（秒）

## 反映済みの見やすさ改善

- 本文色を白に変更
- 疑似ボールド `bold_px: 1`
- layoutの初期値を調整
- brightnessを60へ引き上げ
- demoで動作確認済み設定に合わせた `rgb_matrix` 設定

## X(Twitter)投稿の取得(twscrape)

`config.yaml` の `collector.type` を `twscrape` にすると、`#RSR26` を含む投稿を取得して表示します。

**注意点**

- twscrapeはX公式APIではなく、ログイン済みアカウントのセッションを使ってX内部のGraphQL APIを直接叩く非公式ライブラリです。X利用規約上はグレー〜黒に近い扱いなので、イベント公式アカウント等の重要アカウントでは使わないこと(凍結リスクがあります)。捨てアカウント推奨。
- Xの仕様変更で予告なく動かなくなる可能性があります。本番当日に壊れても慌てないよう、`collector.type` を `mock` に戻せばすぐに従来動作に戻せます。

**事前準備(アカウント登録)**

```bash
pip install -r requirements.txt

# accounts.db を作成し、アカウントを1つ以上登録
twscrape add_accounts accounts.txt username:password:email:email_password
twscrape login_accounts
```

`accounts.txt` は `username:password:email:email_password` 形式で1アカウント1行のテキストファイルです。ログインに成功すると `accounts.db`(SQLite)にセッション情報が保存されます。このファイルはパスワード相当の機密情報を含むので、`.gitignore` に入れて絶対にコミットしないでください。

**config.yaml の設定項目**

```yaml
collector:
  type: "twscrape"
  poll_interval_seconds: 30   # 何秒ごとに新着をチェックするか
  max_buffer: 20               # 表示ローテーションに保持する投稿数の上限
  max_results: 20              # 1回のポーリングで取得する最大件数
  exclude_retweets: true       # リツイートを除外するか
  db_path: "accounts.db"       # 上で作成したaccounts.dbへのパス
```

`poll_interval_seconds` はXから見た通信頻度そのものなので、あまり短くしすぎるとアカウントがレート制限やBAN対象になりやすくなります。30〜60秒程度を推奨します。
