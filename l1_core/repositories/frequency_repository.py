"""Frequency word list repository.

Unlike the other repositories, this one has nothing to do with the
database — it reads static frequency word lists shipped under
l1_core/data/frequency/<language_code>.txt, one word per line,
already ordered from most to least frequent (rank 1 = most frequent).

Data source: lists are expected in the same plain-text, one-word-per-
line format used by projects like hermitdave/FrequencyWords
(https://github.com/hermitdave/FrequencyWords). The small samples
shipped in this repo are placeholders — swap in the full lists for
real use.
"""
from importlib import resources
from pathlib import Path


class FrequencyRepository:
    """Reads word-frequency lists from static data files."""

    def __init__(self, data_dir: Path | None = None):
        if data_dir is not None:
            self._data_dir = data_dir
        else:
            self._data_dir = Path(str(resources.files("l1_core"))) / "data" / "frequency"

    def is_available(self, language_code: str) -> bool:
        """Check whether a frequency list exists for a language.

        Args:
            language_code: ISO 639-1 code of the language to check.

        Returns:
            bool: True if a frequency list file exists.
        """
        return (self._data_dir / f"{language_code.lower()}.txt").exists()

    def get_words(
        self, language_code: str, start_rank: int, end_rank: int
    ) -> list[tuple[int, str]]:
        """Retrieve (rank, word) pairs for an inclusive rank range.

        Ranks are 1-indexed to match how ranks are communicated to
        the user (rank 1 = most frequent word).

        Args:
            language_code: ISO 639-1 code of the language to read.
            start_rank: First rank to include (inclusive).
            end_rank: Last rank to include (inclusive).

        Returns:
            list[tuple[int, str]]: (rank, word) pairs in the range.

        Raises:
            ValueError: If start_rank < 1 or end_rank < start_rank.
            FileNotFoundError: If no frequency list exists for the
                language.
        """
        if start_rank < 1:
            raise ValueError("start_rank must be >= 1")
        if end_rank < start_rank:
            raise ValueError("end_rank must be >= start_rank")

        path = self._data_dir / f"{language_code.lower()}.txt"
        if not path.exists():
            raise FileNotFoundError(
                f"No frequency list found for language '{language_code}' at {path}"
            )

        words: list[tuple[int, str]] = []
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if i < start_rank:
                    continue
                if i > end_rank:
                    break
                word = line.strip().split()[0] if line.strip() else ""
                if word:
                    words.append((i, word))
        return words

    def total_words(self, language_code: str) -> int:
        """Count the total number of words in a language's frequency list.

        Args:
            language_code: ISO 639-1 code of the language to read.

        Returns:
            int: Total word count in the list.

        Raises:
            FileNotFoundError: If no frequency list exists for the
                language.
        """
        path = self._data_dir / f"{language_code.lower()}.txt"
        if not path.exists():
            raise FileNotFoundError(
                f"No frequency list found for language '{language_code}' at {path}"
            )
        with path.open(encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
