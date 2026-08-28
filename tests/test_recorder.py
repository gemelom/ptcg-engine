from __future__ import annotations

from ptcg.core.recorder import EventType, GameRecorder


def test_recorder_persists_aborted_game(tmp_path):
    recorder = GameRecorder(seed=7, output_dir=str(tmp_path))

    recorder.record_aborted("quit")

    assert recorder.events[-1].event_type == EventType.ABORTED
    history = GameRecorder.load(recorder.file_path)
    assert history[-1]["type"] == "aborted"
    assert history[-1]["data"] == {"reason": "quit"}
