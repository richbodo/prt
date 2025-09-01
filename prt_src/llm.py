"""Lightweight wrapper for a Hugging Face causal language model."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from transformers import AutoModelForCausalLM, AutoTokenizer

# Default model – can be overridden in tests by monkeypatching the constant
_MODEL_NAME = "gpt-oss-20b"

_tokenizer: Optional["AutoTokenizer"] = None
_model: Optional["AutoModelForCausalLM"] = None
_generator = None


def _get_hf_token(config: Any) -> Optional[str]:
    """Fetch a Hugging Face token from environment or config."""
    token = os.getenv("HF_TOKEN")
    if token:
        return token
    if isinstance(config, dict):
        return config.get("hf_token")
    return getattr(config, "hf_token", None)


def _ensure_pipeline(config: Any):
    """Load model/tokenizer once and return a generation pipeline."""
    global _tokenizer, _model, _generator
    if _generator is None:
        # Import heavy deps lazily so the module can be imported without them
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        auth = _get_hf_token(config)
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME, use_auth_token=auth)
        _model = AutoModelForCausalLM.from_pretrained(
            _MODEL_NAME,
            use_auth_token=auth,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        _generator = pipeline("text-generation", model=_model, tokenizer=_tokenizer)
    return _generator


def chat(message: str, config: Any) -> str:
    """Generate a response from the configured LLM."""
    generator = _ensure_pipeline(config)
    result = generator(message, max_new_tokens=128)
    return result[0]["generated_text"]
