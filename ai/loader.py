"""Model loader that abstracts backend and device selection."""

from __future__ import annotations

import os
from threading import Lock

from utils.device import pick_device


class ModelWrapper:
    def __init__(self):
        cfg = pick_device()
        self.backend = cfg["backend"]
        self.lock = Lock()
        if self.backend == "transformers":
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            model_name = "mistralai/Mistral-7B-Instruct-v0.2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if cfg["device"] == "cuda" else "cpu",
                torch_dtype="auto",
            )
        else:
            from llama_cpp import Llama  # type: ignore

            path = os.getenv("MISTRAL_GGUF_PATH")
            if not path:
                raise ValueError("MISTRAL_GGUF_PATH not set for llama backend")
            self.tokenizer = None
            self.model = Llama(
                model_path=path,
                n_gpu_layers=cfg["n_gpu_layers"],
                use_mmap=cfg.get("use_mmap", True),
                use_mlock=cfg.get("use_mlock", False),
            )

    def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
        with self.lock:
            if self.backend == "transformers":
                import torch

                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                with torch.no_grad():
                    output = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
                return self.tokenizer.decode(output[0], skip_special_tokens=True)
            else:
                result = self.model(prompt, max_tokens=max_new_tokens)
                return result["choices"][0]["text"]


def load_model() -> ModelWrapper:
    return ModelWrapper()

