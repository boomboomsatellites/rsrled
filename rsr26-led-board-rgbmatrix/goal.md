# goal.md

## プロジェクト名
RSR26 LED Matrix Live Board

## 目的
Raspberry Pi に接続した 128x64 LED マトリクスへ、`#RSR26` に関連する投稿・話題・短い要約を定期的に表示するローカル実行型ツールを作成する。

本プロジェクトは、RSR26 開催期間中だけ稼働することを想定する。X API は有料・仕様変更リスクがあるため、収集部分は差し替え可能な設計にし、まずはローカルで開発・検証できる MVP を優先する。

---

## 背景
- `#RSR26` で投稿された内容を拾い、フェス会場や室内で見られる電光掲示板風に表示したい。
- 表示先は Raspberry Pi に接続予定の 128x64 LED マトリクス。
- LED マトリクスは現在注文中のため、ハードウェア到着前に進められる部分を先に実装する。
- 長いテキストは電車の案内表示のように横スクロール表示する。
- 開催期間中だけの利用を想定するため、堅牢な長期運用よりも、短期間で確実に動くことを優先する。
- Raspberry Pi は Raspberry Pi 3B を使用する想定。
- ショルダーバッグに収めて歩きながら表示する携帯運用も想定する。
- 携帯運用では、電源容量だけでなく、瞬間電流、発熱、重量、配線保護、LEDパネル保護を重視する。

---

## MVP のゴール

### 最小構成で実現したいこと
1. `#RSR26` に関する投稿データを取得、または疑似データで代替できる。
2. 取得したテキストを SQLite に保存する。
3. 表示用メッセージを一定間隔で生成する。
4. LED マトリクス実機が無くても、PC 上のコンソールまたはプレビュー画面で表示確認できる。
5. LED マトリクス到着後、表示出力先を実機に切り替えられる。
6. 長い文字列は電車風に横スクロールできる。
7. 表示内容は `#RSR26 LIVE` のようなタイトル、最新投稿、ホットワード、簡易要約をローテーションできる。
8. 指定時刻になったら、通常ローテーションへ割り込みで定型メッセージを表示できる。

---

## ハードウェア・携帯運用前提

### 想定ハードウェア

```text
Raspberry Pi 3B
128x64 RGB LED Matrix
RGB Matrix HAT / Bonnet 系の変換基板
5V 系モバイルバッテリーまたは 5V 大電流出力電源
ショルダーバッグ
前面保護用アクリル板
短く太めの電源ケーブル
```

### 携帯運用の考え方

ショルダーバッグに収めて歩きながら表示する場合、最大の懸念は Raspberry Pi 3B の消費電力ではなく、LED マトリクスの消費電力、瞬間電流、発熱、物理固定である。

今回の表示は黒背景に文字中心とするため、全面白表示や高輝度動画表示よりは消費電力を抑えやすい。ただし、LED マトリクスは製品によって 5V 大電流を要求するため、モバイルバッテリーの出力仕様と配線を必ず確認する。

### 電源設計方針

推奨しない構成:

```text
モバイルバッテリー
  ↓
Raspberry Pi 3B
  ↓
LED Matrix
```

理由:
- Raspberry Pi 経由で LED マトリクスへ電源供給すると、Pi 側の電源ラインに負荷が集中する。
- LED 表示の瞬間電流で Pi が電圧降下し、再起動や表示乱れが起きる可能性がある。

推奨構成:

```text
モバイルバッテリー / 5V 電源
  ├─ Raspberry Pi 3B
  └─ LED Matrix
```

方針:
- Pi と LED Matrix は 5V を分岐して並列給電する。
- GND は共通化する。
- LED Matrix 側には十分な電流を流せる太め・短めのケーブルを使う。
- 可能なら LED Matrix 側に大容量コンデンサを入れる。
- モバイルバッテリーは 5V 3A 以上、可能なら 5V 4A 以上を検討する。
- USB-C PD 対応バッテリーを使う場合でも、実際に 5V で必要電流が出せるかを確認する。

### 電力削減方針

携帯運用では以下を基本設定にする。

- 背景は黒。
- 全面白表示を避ける。
- 輝度は 30% から 50% 程度を初期値にする。
- 夜間はさらに輝度を下げる。
- 通常表示は文字中心にする。
- アニメーションはスクロール中心にし、派手な全画面点滅は控えめにする。
- Wi-Fi 取得間隔を短くしすぎない。
- 収集処理と表示処理を分離し、表示側は DB の最新データを読む。

### 発熱対策

ショルダーバッグ内は熱がこもりやすいため、以下を前提にする。

- Raspberry Pi 3B にヒートシンクを付ける。
- 可能なら小型ファンも検討する。
- Pi、LED Matrix、バッテリーを密着させない。
- バッグ上部または側面に通気スペースを確保する。
- バッテリーを熱源に密着させない。
- 長時間運用前に PC プレビューだけでなく、実機で発熱確認を行う。

### 重量・固定・安全対策

ショルダーバッグ運用では、重量と固定方法が重要である。

- LED Matrix はバッグ前面に固定する。
- 前面に透明アクリル板を付け、LED 面を保護する。
- ケーブルの抜け防止を行う。
- モバイルバッテリーはバッグ底面または体側に固定し、揺れにくくする。
- LED Matrix の角や基板裏面が身体や荷物に直接触れないようにする。
- 雨天や結露に備え、防滴カバーや透明ポケットを検討する。
- 会場で歩き回る場合、人や物に引っかからない配線にする。

### 実機到着後の確認項目

- [ ] LED Matrix の電源仕様を確認する。
- [ ] HAT / Bonnet が 128x64 パネルのアドレス方式に対応しているか確認する。
- [ ] `rpi-rgb-led-matrix` のサンプルが表示できることを確認する。
- [ ] 輝度 30% / 50% / 80% で表示確認する。
- [ ] スクロール表示で電圧降下や Pi の再起動が起きないことを確認する。
- [ ] バッグに固定した状態でケーブルが抜けないことを確認する。
- [ ] 連続運用時の発熱を確認する。
- [ ] 屋外、夜間、肩掛け移動時の視認性を確認する。

---

## 重要方針

### 1. LED マトリクス未到着でも開発を進める
LED 実機に依存しないよう、表示出力を抽象化する。

以下のような出力先を切り替えられる構成にする。

- `console`: ターミナルに 128x64 相当の表示内容をログ出力
- `pygame` または `pillow`: PC 上で LED マトリクス風プレビュー
- `rgb_matrix`: Raspberry Pi + LED マトリクス実機出力

MVP では、まず `console` と `preview` を実装する。実機用の `rgb_matrix` はインターフェースだけ先に用意し、LED 到着後に実装する。

---

### 2. 収集部分は差し替え可能にする
X は API 料金や仕様変更の影響を受けやすいため、投稿収集モジュールを固定しない。

以下のコレクターを切り替え可能にする。

- `mock_collector`: 開発用の疑似データ
- `manual_json_collector`: 手動作成した JSON/CSV から読み込み
- `playwright_collector`: X の検索画面から取得する実験的実装
- `api_collector`: 将来的に X API 等を使う場合の差し替え口

MVP では `mock_collector` と `manual_json_collector` を必須実装とする。`playwright_collector` は可能なら実装するが、仕様変更で壊れる前提で扱う。

---

### 3. 表示は短く、読みやすくする
128x64 は解像度が低いため、長文をそのまま表示しない。

表示ルール:

- 1画面に詰め込みすぎない。
- 日本語は短く整形する。
- 長い投稿は横スクロールする。
- 絵文字は表示できない可能性があるため、必要に応じて除去または代替する。
- URL は原則表示しない。
- 改行・空白を整える。
- 不適切表現や個人情報が含まれる可能性に備え、NG ワードフィルターを用意する。

---

## 想定アーキテクチャ

```text
+---------------------+
| Collector            |
| - mock               |
| - manual json/csv    |
| - playwright         |
| - api future         |
+----------+----------+
           |
           v
+---------------------+
| SQLite DB            |
| - posts              |
| - display_messages   |
| - hot_words          |
+----------+----------+
           |
           v
+---------------------+
| Analyzer             |
| - normalize text     |
| - extract keywords   |
| - create summaries   |
| - filter NG words    |
+----------+----------+
           |
           v
+---------------------+
| Scheduler            |
| - timed messages     |
| - interrupt queue    |
| - priority handling  |
+----------+----------+
           |
           v
+---------------------+
| Display Controller   |
| - rotate screens     |
| - interrupt display  |
| - scroll text        |
| - brightness config  |
+----------+----------+
           |
           v
+---------------------+
| Output Adapter       |
| - console            |
| - preview            |
| - rgb_matrix future  |
+---------------------+
```

---

## ディレクトリ構成案

```text
rsr26-led-board/
  README.md
  goal.md
  requirements.txt
  .env.example
  config.yaml
  src/
    main.py
    config.py
    db.py
    models.py
    collectors/
      __init__.py
      base.py
      mock_collector.py
      manual_json_collector.py
      playwright_collector.py
    analyzers/
      __init__.py
      text_cleaner.py
      keyword_extractor.py
      message_builder.py
      ng_filter.py
    display/
      __init__.py
      controller.py
      layout.py
      scroller.py
      fonts.py
    scheduler/
      __init__.py
      schedule_loader.py
      timed_message.py
      interrupt_queue.py
    outputs/
      __init__.py
      base.py
      console_output.py
      preview_output.py
      rgb_matrix_output.py
    data/
      sample_posts.json
  tests/
    test_text_cleaner.py
    test_scroller.py
    test_message_builder.py
    test_interrupt_queue.py
    test_schedule_loader.py
```

---

## データモデル

### posts テーブル

```sql
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT,
  posted_at TEXT,
  author_name TEXT,
  text TEXT NOT NULL,
  url TEXT,
  like_count INTEGER DEFAULT 0,
  repost_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(source, external_id)
);
```

### display_messages テーブル

```sql
CREATE TABLE IF NOT EXISTS display_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_type TEXT NOT NULL,
  title TEXT,
  body TEXT NOT NULL,
  priority INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  expires_at TEXT
);
```

### scheduled_messages テーブル

```sql
CREATE TABLE IF NOT EXISTS scheduled_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  trigger_time TEXT NOT NULL,
  title TEXT,
  body TEXT NOT NULL,
  priority INTEGER DEFAULT 100,
  duration_seconds INTEGER DEFAULT 15,
  enabled INTEGER DEFAULT 1,
  fired_at TEXT,
  created_at TEXT NOT NULL
);
```

用途:
- 指定時刻になったら通常表示に割り込ませる定型メッセージを管理する。
- `priority` が高いメッセージほど優先する。
- `fired_at` により、一度だけ表示するメッセージの重複発火を防ぐ。
- 毎時などの繰り返し時報風メッセージは、DB ではなく `config.yaml` 側の schedule 定義でもよい。

---

## 表示モード

### 1. タイトル画面

```text
#RSR26 LIVE
NOW STREAMING
```

用途:
- 起動時
- ローテーションの区切り

---

### 2. 最新投稿スクロール

```text
> Vaundy最高すぎる 音圧やばい
```

仕様:
- 長文は横スクロール。
- 先頭に `>` または `▶` を付ける。
- 1投稿ずつ表示する。
- URL は削除。
- 絵文字は可能なら残すが、フォント非対応の場合は削除。

---

### 3. ホットワード表示

```text
HOT WORDS
1 Vaundy
2 雨
3 フード
```

仕様:
- 直近データから頻出語を抽出する。
- MVP では簡易的な単語カウントで良い。
- 日本語の形態素解析は後回しでも良い。
- まずは設定ファイルに登録したキーワード辞書とのマッチで実装してよい。

---

### 4. 注意喚起表示

```text
CAUTION
雨投稿 増加
カッパ推奨
```

仕様:
- `雨`, `雷`, `寒い`, `混雑`, `列`, `入場`, `落とし物` などのキーワードを検知する。
- 該当投稿が一定数以上あれば注意喚起メッセージを生成する。
- MVP では閾値を `config.yaml` で設定する。

---

### 5. 簡易サマリー表示

```text
RSR26 NOW
フード列長め
雨具あると安心
```

仕様:
- AI API が無くても動くよう、まずはルールベースで作る。
- 将来的に OpenAI / Azure OpenAI / Claude 等へ差し替え可能にする。
- AI 要約は MVP 必須ではない。

---

### 6. 時刻指定の割り込み表示

```text
18:00
SUNSET TIME
そろそろ移動準備
```

用途:
- 何時になったら任意メッセージを割り込み表示する。
- 時報そのものではなく、イベント運営・演出・リマインド用途を想定する。
- 通常の最新投稿スクロールやホットワード表示より優先して表示する。

例:
- `12:00` ランチ時間の案内
- `15:00` 休憩・水分補給の案内
- `18:00` 夕方演出メッセージ
- `20:00` 注目ステージ開始前のメッセージ
- `23:00` 終電・帰宅導線の注意喚起

仕様:
- `config.yaml` に時刻とメッセージを定義できる。
- 指定時刻になったら `interrupt_queue` に追加する。
- 割り込み表示中は通常ローテーションを一時停止する。
- 表示が終わったら通常ローテーションに戻る。
- 同時刻に複数メッセージがある場合は `priority` の高い順に表示する。
- 1回だけ表示するか、毎日同じ時刻に表示するかを選べる。
- MVP では「ローカル時刻ベース、1日内の HH:MM 指定」でよい。
---

## スクロール仕様

### 基本仕様
- 画面幅を超える文字列は右から左にスクロールする。
- スクロール速度は `config.yaml` で変更できる。
- 投稿と投稿の間には十分な空白を入れる。
- 文字が短い場合は中央寄せ、または固定表示にする。

### 実装イメージ

```python
class TextScroller:
    def __init__(self, text: str, width: int, padding: int = 8):
        self.text = text
        self.width = width
        self.padding = padding
        self.offset = 0

    def next_frame(self) -> str:
        padded = " " * self.width + self.text + " " * self.padding
        frame = padded[self.offset:self.offset + self.width]
        self.offset = (self.offset + 1) % len(padded)
        return frame
```

実際の LED 表示ではピクセル幅基準のスクロールが必要になるため、最終的には文字数ではなく描画後のピクセル幅で制御する。

---

## 設定ファイル案

```yaml
app:
  hashtag: "#RSR26"
  refresh_interval_seconds: 300
  display_rotation_seconds: 8
  db_path: "./rsr26.db"

collector:
  type: "mock"
  manual_file: "./src/data/sample_posts.json"

matrix:
  width: 128
  height: 64
  brightness: 40
  output: "preview"
  portable_mode: true
  theme: "train_board"

power:
  device: "raspberry_pi_3b"
  avoid_full_white: true
  default_brightness_day: 50
  default_brightness_night: 30
  low_power_mode: true
  battery_warning_enabled: false
  note: "Pi と LED Matrix は並列給電し、GND を共通化する"

scroll:
  speed: 1
  padding_pixels: 24

schedule:
  enabled: true
  timezone: "Asia/Tokyo"
  messages:
    - name: "lunch_notice"
      time: "12:00"
      title: "RSR26 INFO"
      body: "水分補給とごはん休憩"
      priority: 100
      duration_seconds: 12
      repeat: "daily"
    - name: "sunset_notice"
      time: "18:00"
      title: "SUNSET TIME"
      body: "夕方の空も楽しもう"
      priority: 100
      duration_seconds: 15
      repeat: "daily"
    - name: "last_notice"
      time: "23:00"
      title: "RSR26 INFO"
      body: "帰り道と足元に注意"
      priority: 120
      duration_seconds: 15
      repeat: "daily"

filters:
  remove_urls: true
  remove_mentions: false
  max_text_length: 120
  ng_words:
    - "dummy_ng_word"

keywords:
  caution:
    - "雨"
    - "雷"
    - "寒い"
    - "混雑"
    - "列"
    - "入場"
    - "落とし物"
  food:
    - "ラーメン"
    - "カレー"
    - "ビール"
    - "フード"
  music:
    - "最高"
    - "音圧"
    - "ライブ"
    - "ステージ"
```

---

## 開発優先順位

### Phase 1: LED なしで動く MVP
- [ ] プロジェクト雛形を作成
- [ ] `config.yaml` 読み込み
- [ ] SQLite 初期化
- [ ] `mock_collector` 実装
- [ ] `manual_json_collector` 実装
- [ ] 投稿テキストの正規化
- [ ] URL 除去
- [ ] NG ワードフィルター
- [ ] 表示メッセージ生成
- [ ] コンソール表示
- [ ] 横スクロール処理
- [ ] 時刻指定の割り込み表示
- [ ] `config.yaml` の schedule 定義読み込み
- [ ] 割り込み表示後に通常ローテーションへ復帰
- [ ] サンプル投稿データでローテーション表示

### Phase 2: PC プレビュー
- [ ] `pygame` または `Pillow` で 128x64 プレビュー画面を作る
- [ ] LED 風のドット表示にする
- [ ] フォントサイズを調整
- [ ] 日本語表示の可読性を確認
- [ ] スクロール速度を調整

### Phase 3: 収集機能の拡張
- [ ] Playwright 収集の検証
- [ ] 検索キーワード `#RSR26` の取得
- [ ] 重複投稿の除外
- [ ] 取得失敗時に前回データを使い続ける
- [ ] 手動 JSON/CSV フォールバックを用意

### Phase 4: LED 実機対応
- [ ] `rpi-rgb-led-matrix` の導入手順を README に追記
- [ ] `rgb_matrix_output.py` を実装
- [ ] 輝度調整
- [ ] 起動時の自動実行
- [ ] systemd service 化

### Phase 4.5: ショルダーバッグ携帯運用対応
- [ ] Raspberry Pi 3B 前提の README を追記
- [ ] Pi と LED Matrix の並列給電構成を README に図示
- [ ] `portable_mode` を追加し、初期輝度を低めにする
- [ ] 黒背景・文字中心の省電力テーマを用意
- [ ] 夜間向けの低輝度設定を用意
- [ ] バッグ固定時のチェックリストを README に追加
- [ ] 前面アクリル板・配線保護・通気の注意点を README に追加
- [ ] 実機到着後の電圧降下・発熱・視認性確認手順を追加


### Phase 5: 表示演出
- [ ] HOT 表示
- [ ] CAUTION 表示
- [ ] 投稿数の簡易グラフ
- [ ] 点滅演出
- [ ] 色分け
- [ ] 電車案内板風テーマ

---

## GitHub Copilot への実装指示

以下の方針で実装してください。

1. Python で実装する。
2. Raspberry Pi 実機が無くても開発できるよう、出力先を抽象化する。
3. 最初は `mock_collector` と `console_output` で動作する MVP を作る。
4. 128x64 LED マトリクスを想定した表示レイアウトにする。
5. 長いテキストは横スクロールできるようにする。
6. 投稿データは SQLite に保存する。
7. 設定値は `config.yaml` から読み込む。
8. X API やスクレイピングに強く依存しない設計にする。
9. `playwright_collector` は実験的扱いにし、取得できない場合でもアプリ全体が落ちないようにする。
10. テストしやすいように、collector / analyzer / display / output を分離する。
11. 日本語テキストの表示を想定する。
12. URL、改行、連続空白を整形する。
13. 不適切表現を除外できる NG ワードフィルターを用意する。
14. 指定時刻になったら通常ローテーションへ割り込みで定型メッセージを表示できるようにする。
15. 割り込み表示は `scheduler` と `interrupt_queue` として通常表示ロジックから分離する。
16. LED 到着後に `rgb_matrix_output.py` を差し替え実装できるよう、インターフェースを先に定義する。
17. Raspberry Pi 3B を前提に README と設定例を書く。
18. ショルダーバッグ携帯運用を想定し、省電力表示、低輝度設定、黒背景テーマを用意する。
19. 電源は Pi 経由ではなく Pi と LED Matrix への並列給電を前提に注意書きを入れる。
20. 発熱、重量、配線保護、前面アクリル板による LED 保護を README の運用注意に入れる。

---

## 最初に実装するコマンド

```bash
python -m src.main --collector mock --output console
```

期待動作:
- サンプル投稿を読み込む。
- テキストを整形する。
- 表示用メッセージを作る。
- コンソール上で `#RSR26 LIVE`、最新投稿、ホットワードをローテーション表示する。
- 長い投稿は横スクロール風に表示する。
- `config.yaml` の schedule に定義された時刻になったら割り込みメッセージを表示する。

---

## サンプル投稿データ

```json
[
  {
    "external_id": "sample-001",
    "posted_at": "2026-08-01T12:00:00+09:00",
    "author_name": "sample_user_1",
    "text": "#RSR26 会場着いた！空気が最高すぎる",
    "url": ""
  },
  {
    "external_id": "sample-002",
    "posted_at": "2026-08-01T12:05:00+09:00",
    "author_name": "sample_user_2",
    "text": "#RSR26 フードエリアの列が長くなってきた。早めに行った方がよさそう",
    "url": ""
  },
  {
    "external_id": "sample-003",
    "posted_at": "2026-08-01T12:10:00+09:00",
    "author_name": "sample_user_3",
    "text": "#RSR26 雨が少し降ってきたのでカッパあると安心",
    "url": ""
  }
]
```

---

## 非機能要件

### 安定性
- 収集に失敗しても表示処理は継続する。
- DB が壊れた場合は明確なエラーを出す。
- 表示データが空の場合は待機画面を表示する。
- 割り込みメッセージ処理で例外が発生しても通常表示へ戻る。

### 運用性
- 設定は `config.yaml` で変更できる。
- ログを標準出力に出す。
- systemd 化しやすい構成にする。

### 可搬性
- 開発は PC で可能にする。
- Raspberry Pi 依存コードは `outputs/rgb_matrix_output.py` に隔離する。

### 表示品質
- 文字は大きく、短く、読みやすくする。
- 長文はスクロールする。
- 1画面に過剰な情報を詰め込まない。

---

## 既知のリスク

### X データ取得リスク
- X API は有料で、取得コストが発生する可能性がある。
- スクレイピングは仕様変更で壊れやすい。
- 利用規約やアクセス制限に注意する必要がある。

対策:
- collector を差し替え可能にする。
- 手動 JSON/CSV 入力 fallback を用意する。
- 収集失敗時も既存データで表示を継続する。

### 日本語表示リスク
- LED マトリクスで日本語フォントが読みにくい可能性がある。
- 128x64 では長文表示に向かない。

対策:
- 短文化する。
- 横スクロールする。
- PC プレビューでフォントと速度を先に検証する。

### 携帯運用リスク
- ショルダーバッグ内で熱がこもる可能性がある。
- LED Matrix の瞬間電流により Pi が再起動する可能性がある。
- ケーブル抜けや接触不良で表示が乱れる可能性がある。
- 歩行中の振動や衝撃で LED Matrix が破損する可能性がある。
- 雨天や結露で電子部品が故障する可能性がある。

対策:
- Pi と LED Matrix を並列給電にする。
- 輝度を抑え、黒背景の文字表示を基本にする。
- ヒートシンク、通気、バッテリー配置を考慮する。
- 前面アクリル板と配線固定を行う。
- 防滴カバーを検討する。

### ハードウェア未到着リスク
- LED マトリクス到着まで実機確認できない。

対策:
- console / preview 出力を先に実装する。
- rgb_matrix 出力は adapter として後から追加する。

---

## 完了条件

MVP 完了条件:

- `python -m src.main --collector mock --output console` が動作する。
- サンプル投稿が SQLite に保存される。
- 表示メッセージが生成される。
- `#RSR26 LIVE`、最新投稿、ホットワードがローテーション表示される。
- 長文投稿が横スクロール表示される。
- 指定時刻の割り込みメッセージが通常ローテーションより優先して表示される。
- 割り込み表示後、通常ローテーションへ自動復帰する。
- LED 実機なしでプレビュー確認できる。
- 実機用 output adapter のインターフェースが存在する。
- Raspberry Pi 3B とショルダーバッグ携帯運用を前提にした README の注意事項がある。
- `portable_mode` により低輝度・黒背景中心の表示設定へ切り替えられる。

---

## 将来追加したい機能

- AI 要約
- 投稿数推移の表示
- 急上昇ワード検知
- 天気・混雑・落とし物の注意喚起
- ボタンやキーボードによる表示モード切り替え
- 電車案内板風テーマ
- フェスっぽいカラーテーマ
- Bluesky / Mastodon 等の別ソース対応
- Web 管理画面
- 手動で任意メッセージを差し込む機能
- タイムテーブル連動の自動割り込み表示
- カウントダウン表示

---

## Copilot に最初に依頼する内容

この `goal.md` に従って、まず Phase 1 の MVP を実装してください。

優先順位は以下です。

1. プロジェクト構成を作る
2. 設定ファイルを読む
3. SQLite に投稿を保存する
4. mock データを読み込む
5. テキストを整形する
6. 表示メッセージを作る
7. コンソールに 128x64 LED 表示を想定した内容を出す
8. 長文を横スクロール表示する
9. 指定時刻になったら割り込みメッセージを表示する
10. 出力先 adapter を定義し、将来 Raspberry Pi 実機出力へ差し替えられるようにする
11. Raspberry Pi 3B とショルダーバッグ携帯運用を前提にした README の電源・発熱・固定・保護注意を追加する

LED マトリクス実機はまだ無いため、実機制御は後回しで構いません。まず PC 上で表示ロジックとデータ処理が確認できる状態を作ってください。
