from pathlib import Path
import yaml

def load_config(path='config.yaml'):
    cfg = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    for key in ['app', 'storage', 'matrix']:
        if key not in cfg:
            raise ValueError(f'Missing config section: {key}')
    return cfg
