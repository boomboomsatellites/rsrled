from src.config import load_config
from src.models import DisplayMessage
from src.outputs.rgb_matrix_output import render_message_image

def test_render_message_image_size():
    img = render_message_image(load_config('config.yaml'), DisplayMessage('title', 'T', 'B'))
    assert img.size == (128, 64)
