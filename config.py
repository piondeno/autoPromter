import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
SESSION_DIR = BASE_DIR / "session"
DATA_REQUIRE_LIST_DIR = BASE_DIR / "dataRequireList"

GEMINI_URL = "https://gemini.google.com/"

TIMEOUT = 30
IMPLICIT_WAIT = 10

INPUT_DELAY_MIN = 0.05
INPUT_DELAY_MAX = 0.15

AFTER_SUBMIT_DELAY = 3

DATA_KEEP_COUNT = 100
