"""The Whisper model shared by transcribe.py and words.py (import it after their PyAV patch).

The model (about 1.6 GB) is downloaded once into <toolkit>\\models\\. Downloading through the Hugging Face cache instead
keeps two full copies on Windows without symlink support (blobs\\ + snapshots\\, about 3.2 GB), so the cache is only
used when an older install already put the model there.
"""
import os, warnings
# faster-whisper still passes local_dir_use_symlinks, which huggingface_hub now ignores (and warns about)
warnings.filterwarnings("ignore", message=".*local_dir_use_symlinks.*")
from faster_whisper import WhisperModel
from faster_whisper.utils import download_model

MODEL = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "faster-whisper-large-v3-turbo")


def model_path():
    if os.path.exists(os.path.join(MODEL_DIR, "model.bin")):
        return MODEL_DIR
    try:                                     # already in the Hugging Face cache from an earlier version: reuse it
        return download_model(MODEL, local_files_only=True)
    except Exception:
        pass
    print("第一次使用：下載語音辨識模型（約 1.6 GB，只需要一次）...", flush=True)
    return download_model(MODEL, output_dir=MODEL_DIR)


def load():
    return WhisperModel(model_path(), device="cpu", compute_type="int8", cpu_threads=max(2, (os.cpu_count() or 4) - 2))
