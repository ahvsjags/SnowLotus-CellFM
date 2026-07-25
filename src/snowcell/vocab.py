from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SPECIAL_TOKENS = ("<pad>", "<cls>", "<mask>", "<unk>")


@dataclass(frozen=True)
class Vocabulary:
    tokens: tuple[str, ...]

    @classmethod
    def build(cls, genes: Iterable[str]) -> "Vocabulary":
        unique = sorted({str(gene) for gene in genes if str(gene)})
        return cls(tokens=tuple(SPECIAL_TOKENS) + tuple(unique))

    @classmethod
    def from_list(cls, tokens: list[str]) -> "Vocabulary":
        if tuple(tokens[: len(SPECIAL_TOKENS)]) != SPECIAL_TOKENS:
            raise ValueError(f"基因词表必须以特殊 token {SPECIAL_TOKENS} 开头")
        return cls(tokens=tuple(tokens))

    @property
    def stoi(self) -> dict[str, int]:
        return {token: index for index, token in enumerate(self.tokens)}

    @property
    def pad_id(self) -> int:
        return 0

    @property
    def cls_id(self) -> int:
        return 1

    @property
    def mask_id(self) -> int:
        return 2

    @property
    def unk_id(self) -> int:
        return 3

    def encode(self, genes: Iterable[str]) -> list[int]:
        lookup = self.stoi
        return [lookup.get(str(gene), self.unk_id) for gene in genes]

    def decode(self, ids: Iterable[int]) -> list[str]:
        return [self.tokens[int(index)] for index in ids]

    def __len__(self) -> int:
        return len(self.tokens)


@dataclass(frozen=True)
class LabelVocabulary:
    labels: tuple[str, ...]

    @classmethod
    def build(cls, labels: Iterable[str]) -> "LabelVocabulary":
        unique = sorted({str(label) for label in labels if str(label)})
        if not unique:
            raise ValueError("标签词表不能为空")
        return cls(labels=tuple(unique))

    @classmethod
    def from_list(cls, labels: list[str]) -> "LabelVocabulary":
        return cls(labels=tuple(labels))

    @property
    def stoi(self) -> dict[str, int]:
        return {label: index for index, label in enumerate(self.labels)}

    def encode(self, labels: Iterable[str], unknown_value: int = -1) -> list[int]:
        lookup = self.stoi
        return [lookup.get(str(label), unknown_value) for label in labels]

    def decode(self, ids: Iterable[int], unknown_label: str = "unknown") -> list[str]:
        result = []
        for index in ids:
            index = int(index)
            result.append(self.labels[index] if 0 <= index < len(self.labels) else unknown_label)
        return result

    def __len__(self) -> int:
        return len(self.labels)

