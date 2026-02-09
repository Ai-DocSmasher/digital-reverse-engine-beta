import argparse
import soundfile as sf
import numpy as np
import librosa

from core.hybrid.pipeline import process_audio
from gui_player import hybrid_mel_acf_tempo, detect_tempo_fallback  # or move these to a shared module


def main():
    parser = argparse.ArgumentParser(
        description="Digital Reverse Engine — CLI (Hybrid Tempo)"
    )
    parser.add_argument("-i", "--input", required=True, help="Input audio file (wav/mp3)")
    parser.add_argument("-o", "--output", required=True, help="Output WAV file")
    parser.add_argument("-m", "--mode", default="HQ_REVERSE",
                        choices=["TRUE_REVERSE", "HQ_REVERSE", "QBEAT_REVERSE", "TATUM_REVERSE", "STUDIO_REVERSE"],
                        help="Processing mode")
    parser.add_argument("--tempo", type=float, default=None, help="Tempo in BPM (leave empty for hybrid auto-tempo)")
    parser.add_argument("--beats-per-bar", type=int, default=4, help="Beats per bar")
    parser.add_argument("--bars-per-slice", type=int, default=1, help="Bars per slice (studio mode)")
    parser.add_argument("--tatum-fraction", type=float, default=0.25, help="Tatum fraction (tatum mode)")

    args = parser.parse_args()

    audio, sr = sf.read(args.input)
    audio = audio.astype(np.float32)

    tempo = args.tempo
    if tempo is None:
        tempo = hybrid_mel_acf_tempo(audio, sr)
        if tempo is None:
            tempo = detect_tempo_fallback(audio, sr)
        if tempo is None:
            tempo = 120.0
        print(f"[DRE CLI] Tempo: {tempo:.2f} BPM")
    else:
        print(f"[DRE CLI] Using user tempo: {tempo:.2f} BPM")

    processed = process_audio(
        audio,
        sample_rate=sr,
        mode=args.mode,
        tempo=tempo,
        beats_per_bar=args.beats_per_bar,
        bars_per_slice=args.bars_per_slice,
        tatum_fraction=args.tatum_fraction
    )

    sf.write(args.output, processed, sr)
    print(f"[DRE CLI] Saved to: {args.output}")


if __name__ == "__main__":
    main()
