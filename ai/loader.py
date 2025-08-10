from __future__ import annotations
import os
from utils.device import pick_device


def load_model():
    cfg = pick_device()
    if cfg["backend"] == "transformers":
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto" if cfg["device"] == "cuda" else "cpu",
            torch_dtype="auto",
        )
        return {"backend": "transformers", "model": model, "tokenizer": tokenizer}
    else:
        from llama_cpp import Llama  # type: ignore

        path = os.getenv("MISTRAL_GGUF_PATH")
        if not path:
            raise ValueError("MISTRAL_GGUF_PATH not set for llama backend")
        model = Llama(
            model_path=path,
            n_gpu_layers=cfg["n_gpu_layers"],
            use_mmap=cfg["use_mmap"],
            use_mlock=cfg["use_mlock"],
        )
        return {"backend": "llama", "model": model, "tokenizer": None}
