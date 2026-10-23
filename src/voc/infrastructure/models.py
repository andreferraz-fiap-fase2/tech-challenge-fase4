"""Modelos locais com revisões congeladas e execução em CPU."""

import os
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

from voc.infrastructure.storage import read_json

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def fetch_models(root: Path) -> None:
    settings = read_json(root / "config/models.json")
    for kind in ("embedding", "generation"):
        snapshot_download(
            repo_id=str(settings[f"{kind}_model"]),
            revision=str(settings[f"{kind}_revision"]),
            local_dir=root / "models" / kind,
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken", "*.jinja"],
            ignore_patterns=["onnx/*", "openvino/*"],
        )


class LocalEmbedder:
    def __init__(self, root: Path) -> None:
        self.settings = read_json(root / "config/models.json")
        torch.set_num_threads(int(self.settings["threads"]))
        self.model = SentenceTransformer(
            str(root / "models/embedding"), device="cpu", local_files_only=True
        )

    def encode(self, texts: list[str], progress: bool = False) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=progress,
            convert_to_numpy=True,
        ).astype(np.float32)

    def chunks(self, text: str) -> list[str]:
        offsets = self.model.tokenizer(
            text, add_special_tokens=False, return_offsets_mapping=True, verbose=False
        )["offset_mapping"]
        size = int(self.settings["document_tokens"])
        overlap = int(self.settings["chunk_overlap_tokens"])
        if not 0 <= overlap < size < self.model.max_seq_length:
            raise ValueError("Janela de tokens incompatível com o modelo de embeddings.")
        chunks = []
        for start in range(0, len(offsets), size - overlap):
            stop = min(start + size, len(offsets))
            chunks.append(text[offsets[start][0] : offsets[stop - 1][1]])
            if stop == len(offsets):
                break
        return chunks


class LocalGenerator:
    def __init__(self, root: Path) -> None:
        self.settings = read_json(root / "config/models.json")
        self.name = str(self.settings["generation_model"])
        self.root = root
        self.tokenizer = None
        self.model = None

    def generate(self, prompt: str) -> str:
        if self.model is None:
            torch.set_num_threads(int(self.settings["threads"]))
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.root / "models/generation", local_files_only=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.root / "models/generation",
                local_files_only=True,
                dtype=torch.float32,
            ).eval()
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=int(self.settings["max_new_tokens"]),
                do_sample=False,
                temperature=1.0,
                top_p=1.0,
                top_k=50,
                repetition_penalty=1.12,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(
            generated[0, inputs.input_ids.shape[1] :], skip_special_tokens=True
        ).strip()
