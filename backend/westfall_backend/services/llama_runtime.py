from typing import Generator
from .settings import Settings
from loguru import logger

try:
    from llama_cpp import Llama
except Exception as e:
    Llama = None  # lazy fail; log later

class LlamaRuntime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = None

    def ensure_loaded(self):
        if self.llm is None:
            if not self.settings.model_path:
                raise RuntimeError("Model path not set (WESTFALL_MODEL_PATH).")
            if Llama is None:
                raise RuntimeError("llama-cpp-python not available.")
            logger.info("Loading model: {}", self.settings.model_path)
            self.llm = Llama(
                model_path=self.settings.model_path,
                n_ctx=self.settings.n_ctx,
                n_threads=self.settings.n_threads,
                n_gpu_layers=self.settings.n_gpu_layers or 0,
                logits_all=False,
                verbose=False,
            )

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        self.ensure_loaded()
        out = self.llm(prompt, max_tokens=max_tokens, stream=False)
        return out["choices"][0]["text"]

    def stream(self, prompt: str, max_tokens: int = 256) -> Generator[str, None, None]:
        self.ensure_loaded()
        for chunk in self.llm(prompt, max_tokens=max_tokens, stream=True):
            yield chunk["choices"][0]["text"] or ""

    def is_loaded(self) -> bool:
        return self.llm is not None