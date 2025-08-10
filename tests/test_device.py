from utils import device
import types
import importlib
import sys


def test_pick_backend_default(monkeypatch):
    monkeypatch.delenv("BACKEND", raising=False)
    importlib.reload(device)
    assert device.pick_backend() == "transformers"


def test_pick_backend_env(monkeypatch):
    monkeypatch.setenv("BACKEND", "llama")
    importlib.reload(device)
    assert device.pick_backend() == "llama"


def test_pick_device_cpu(monkeypatch):
    fake_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: False)
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setenv("BACKEND", "transformers")
    importlib.reload(device)
    cfg = device.pick_device()
    assert cfg["device"] == "cpu"


def test_pick_device_cuda(monkeypatch):
    fake_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: True)
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setenv("BACKEND", "transformers")
    importlib.reload(device)
    cfg = device.pick_device()
    assert cfg["device"] == "cuda"


def test_pick_device_llama(monkeypatch):
    fake_llama = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama)
    monkeypatch.setenv("BACKEND", "llama")
    importlib.reload(device)
    cfg = device.pick_device()
    assert cfg["backend"] == "llama" and cfg["n_gpu_layers"] >= 0
