"""Helpers to pick AI backend and device."""

from __future__ import annotations

import os
from typing import Any, Dict


def pick_backend() -> str:
    b = os.getenv("BACKEND")
    return b if b in {"transformers", "llama"} else "transformers"


def pick_device() -> Dict[str, Any]:
    backend = pick_backend()
    if backend == "transformers":
        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                return {"backend": "transformers", "device": "cuda", "dtype": "auto"}
        except Exception:
            pass
        return {"backend": "transformers", "device": "cpu", "dtype": "auto"}
    else:
        try:
            import llama_cpp  # noqa: F401

            return {
                "backend": "llama",
                "n_gpu_layers": 35,
                "use_mmap": True,
                "use_mlock": False,
            }
        except Exception:
            return {
                "backend": "llama",
                "n_gpu_layers": 0,
                "use_mmap": True,
                "use_mlock": False,
            }
