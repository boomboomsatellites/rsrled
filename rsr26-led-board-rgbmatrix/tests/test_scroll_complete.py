from src.display.marquee import MarqueeState

def test_long_message_eventually_completes():
    s = MarqueeState()
    done = False
    for _ in range(200):
        _, done = s.frame('k', text_width=200, panel_width=128, step=10, end_hold=2, short_frames=5)
        if done:
            break
    assert done


def test_short_message_completes_after_short_frames():
    s = MarqueeState()
    results = [s.frame('k', text_width=20, panel_width=128, short_frames=3)[1] for _ in range(3)]
    assert results == [False, False, True]
