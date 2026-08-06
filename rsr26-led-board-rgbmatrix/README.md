# RSR26 LED Matrix Live Board for Raspberry Pi 3B

`./demo --led-rows=64 --led-cols=128 --led-chain=1 --led-slowdown-gpio=3 --led-brightness=20 --led-no-hardware-pulse --led-multiplexing=0 -D 0` で表示できた設定に合わせて `rgb_matrix_output.py` を更新した版です。

## 実機表示

```bash
pip install -r requirements.txt
sudo -E python3 -m src.main --collector mock --output rgb_matrix --frames 1000 --sleep 0.05
```

または:

```bash
./scripts/run_rgb_matrix.sh
```

## 重要設定

```yaml
rgb_matrix:
  rows: 64
  cols: 128
  chain_length: 1
  gpio_slowdown: 3
  brightness: 20
  disable_hardware_pulsing: true
  multiplexing: 0
  hardware_mapping: "regular"
```

## 日本語フォント

日本語が豆腐になる場合:

```bash
sudo apt install fonts-noto-cjk
```
