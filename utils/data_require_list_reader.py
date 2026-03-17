import re
from pathlib import Path
from typing import List, Dict, Optional

import config


def list_md_files() -> List[Path]:
    if not config.DATA_REQUIRE_LIST_DIR.exists():
        config.DATA_REQUIRE_LIST_DIR.mkdir(parents=True, exist_ok=True)
        return []
    return sorted(config.DATA_REQUIRE_LIST_DIR.glob("*.md"))


def parse_md_file(file_path: Path) -> Dict:
    result = {
        "fred_api_key": None,
        "fred_series": [],
        "macromicro_urls": [],
        "stooq_urls": []
    }

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    api_key_match = re.search(r'FRED\s*API\s*Key\s*[:：]\s*(\S+)', content, re.IGNORECASE)
    if api_key_match:
        result["fred_api_key"] = api_key_match.group(1)

    lines = content.split('\n')
    in_fred_section = False
    in_macromicro_section = False
    in_stooq_section = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if line_stripped.startswith('## ') and 'FRED' in line_stripped.upper():
            in_fred_section = True
            in_macromicro_section = False
            in_stooq_section = False
            continue
        elif line_stripped.startswith('## ') and 'macromicro' in line_stripped.lower():
            in_fred_section = False
            in_macromicro_section = True
            in_stooq_section = False
            continue
        elif line_stripped.startswith('## ') and 'stooq' in line_stripped.lower():
            in_fred_section = False
            in_macromicro_section = False
            in_stooq_section = True
            continue

        if in_fred_section and not line_stripped.startswith('#'):
            series_match = re.search(r'[（(]\s*([A-Z0-9]+)\s*[）)]\s*$', line_stripped)
            if not series_match:
                series_match = re.search(r':\s*([A-Z0-9]+)\s*$', line_stripped)
            if series_match:
                series_id = series_match.group(1)
                name_part = line_stripped
                for sep in ['（', '(', '：', ':']:
                    if sep in name_part:
                        name_part = name_part.split(sep)[0]
                        break
                name = name_part.strip()
                result["fred_series"].append({
                    "name": name,
                    "series_id": series_id
                })

        if in_macromicro_section and not line_stripped.startswith('#'):
            url_match = re.search(r'https?://[^\s]+', line_stripped)
            if url_match:
                url = url_match.group(0)
                name = line_stripped.split('http')[0].strip()
                name = re.sub(r'^\d+\.?\s*', '', name).strip()
                result["macromicro_urls"].append({
                    "name": name,
                    "url": url
                })

        if in_stooq_section and not line_stripped.startswith('#'):
            url_match = re.search(r'https?://[^\s]+', line_stripped)
            if url_match:
                url = url_match.group(0)
                name = line_stripped.split('http')[0].strip()
                name = re.sub(r'^\d+\.?\s*', '', name).strip()
                name = name.rstrip(' :：').strip()
                result["stooq_urls"].append({
                    "name": name,
                    "url": url
                })

    return result


def get_output_dir(md_file_name: str) -> Path:
    output_dir = config.DATA_REQUIRE_LIST_DIR / md_file_name.replace('.md', '')
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
