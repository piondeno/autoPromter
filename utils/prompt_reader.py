from pathlib import Path
from typing import List

import config


def list_prompt_files() -> List[Path]:
    if not config.PROMPTS_DIR.exists():
        config.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        return []
    return sorted(config.PROMPTS_DIR.glob("*.txt"))


def read_prompts(file_path: Path) -> List[str]:
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                clean_line = line.replace("\n", " ").replace("\r", "").replace("\t", "   ")
                if "\n" in line or "\r" in line or "\t" in line:
                    print(f"Warning: Prompt contains special characters, cleaned: {clean_line[:50]}...")
                prompts.append(clean_line)
    return prompts
