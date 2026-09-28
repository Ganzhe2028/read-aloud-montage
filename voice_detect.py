"""Read a JSON list of local files on stdin; return local speech intervals as JSON."""

from __future__ import annotations

import json
import sys

from faster_whisper.audio import decode_audio
from faster_whisper.vad import VadOptions, get_speech_timestamps


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    paths = json.load(sys.stdin)
    options = VadOptions(
        threshold=0.5,
        min_speech_duration_ms=250,
        max_speech_duration_s=20.0,
        min_silence_duration_ms=500,
        speech_pad_ms=150,
    )
    results = []
    for path in paths:
        try:
            audio = decode_audio(path, sampling_rate=16000)
            duration = len(audio) / 16000
            chunks = get_speech_timestamps(audio, options, sampling_rate=16000)
            results.append({
                "path": path,
                "duration": duration,
                "speech": [[chunk["start"] / 16000, chunk["end"] / 16000] for chunk in chunks],
            })
        except Exception as error:
            results.append({"path": path, "error": f"{type(error).__name__}: {error}"})
    json.dump(results, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
