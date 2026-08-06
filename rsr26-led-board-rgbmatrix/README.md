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

## 反映済みの見やすさ改善

- 本文色を白に変更
- 疑似ボールド `bold_px: 1`
- layoutの初期値を調整
- brightnessを60へ引き上げ
- demoで動作確認済み設定に合わせた `rgb_matrix` 設定
