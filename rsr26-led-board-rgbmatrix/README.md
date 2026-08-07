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
