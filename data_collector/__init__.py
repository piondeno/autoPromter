import json
import math
import time
import random
import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import requests


def clean_value(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    if isinstance(val, (int, float)):
        return val
    return val


def collect_fred_data(api_key: str, series_ids: List[str], limit: int = 50) -> Dict[str, pd.DataFrame]:
    results = {}

    for series_id in series_ids:
        print(f"  Downloading FRED: {series_id}...")
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": api_key,
                "observation_start": "1900-01-01",
                "limit": limit,
                "sort_order": "desc",
                "file_type": "json"
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "observations" in data:
                observations = data["observations"]
                df = pd.DataFrame(observations)
                if not df.empty:
                    df = df[['date', 'value']]
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    results[series_id] = df
                    print(f"    Got {len(df)} records")
                else:
                    print(f"    No data found")
            else:
                print(f"    Error: {data.get('error_message', 'Unknown error')}")

        except Exception as e:
            print(f"    Error fetching {series_id}: {e}")

        time.sleep(random.uniform(0.5, 1.0))

    return results


def collect_macromicro_data(driver, urls: List[Dict], limit: int = 50) -> Dict[str, pd.DataFrame]:
    results = {}

    print("\n" + "=" * 50)
    print("Macromicro data download")
    print("=" * 50)
    
    driver.get("https://www.macromicro.me/")
    time.sleep(3)
    print("Please log in to macromicro in the browser if needed.")
    input("Press Enter after you have logged in to start downloading...")
    print("Starting download...\n")

    for item in urls:
        url = item["url"]
        name = item["name"]
        print(f"  Downloading macromicro: {name}...")

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                driver.get(url)
                time.sleep(5)

                is_captcha = driver.execute_script(
                    "return document.body.innerText.includes('robot') || "
                    "document.body.innerText.includes('驗證') || "
                    "document.body.innerText.includes('captcha') || "
                    "document.getElementById('cf-challenge') !== null || "
                    "document.querySelector('.cf-challenge') !== null;"
                )

                if is_captcha:
                    print(f"    Detected bot verification. Please complete the verification in browser.")
                    input(f"    Press Enter after completing verification...")
                    retry_count += 1
                    continue

                data_points = driver.execute_script(
                    "return Highcharts && Highcharts.charts[0] && Highcharts.charts[0].series[0] ? "
                    "Highcharts.charts[0].series[0].data.map(function(point) {"
                    "  return {x: point.x, y: point.y};"
                    "}) : null;"
                )

                if data_points:
                    temp_list = []
                    for row in data_points:
                        temp_list.append({
                            'Date': datetime.datetime.fromtimestamp(0) + datetime.timedelta(seconds=row['x']/1000-8*60*60),
                            'Data': row['y']
                        })

                    df = pd.DataFrame(temp_list)
                    df = df.sort_values('Date', ascending=False)
                    df = df.head(limit)

                    results[name] = df
                    print(f"    Got {len(df)} records")
                    break
                else:
                    print(f"    No data found on page")
                    break

            except Exception as e:
                print(f"    Error fetching {name}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"    Retrying... ({retry_count}/{max_retries})")
                    time.sleep(2)

        if name not in results:
            print(f"    Failed after {max_retries} attempts")

        time.sleep(random.uniform(0.5, 1.0))

    return results


def save_to_json(all_data: Dict[str, pd.DataFrame], output_dir: Path, md_file_name: str):
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "data.json"

    combined_data = {}
    for name, df in all_data.items():
        df_json = df.to_dict(orient='records')
        cleaned_records = []
        for record in df_json:
            cleaned_record = {}
            for key, val in record.items():
                cleaned_val = clean_value(val)
                if isinstance(cleaned_val, datetime.datetime):
                    cleaned_record[key] = cleaned_val.isoformat()
                elif cleaned_val is not None:
                    cleaned_record[key] = cleaned_val
            cleaned_records.append(cleaned_record)
        combined_data[name] = cleaned_records

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"  Saved all data to: {output_file.name}")


def collect_stooq_data(urls: List[Dict], limit: int = 50) -> Dict[str, pd.DataFrame]:
    results = {}

    for item in urls:
        url = item["url"]
        name = item["name"]
        print(f"  Downloading stooq: {name}...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            if not df.empty:
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                elif 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')

                df = df.sort_values('Date' if 'Date' in df.columns else 'date', ascending=False)
                df = df.head(limit)

                results[name] = df
                print(f"    Got {len(df)} records")
            else:
                print(f"    No data found")

        except Exception as e:
            print(f"    Error fetching {name}: {e}")

        time.sleep(random.uniform(0.5, 1.0))

    return results


def collect_all_data(api_key: Optional[str], fred_series: List[Dict],
                      macromicro_urls: List[Dict], driver,
                      output_dir: Path, limit: int = 50,
                      stooq_urls: Optional[List[Dict]] = None) -> bool:
    print("\n" + "=" * 50)
    print("Starting data collection...")
    print("=" * 50)

    all_data = {}

    if api_key and fred_series:
        print(f"\n[FRED Data] Fetching {len(fred_series)} series (limit: {limit} most recent)...")
        series_ids = [s["series_id"] for s in fred_series]
        fred_data = collect_fred_data(api_key, series_ids, limit)
        all_data.update(fred_data)
        if not fred_data:
            print("No FRED data collected")
    else:
        print("\nSkipping FRED data (no API key or series defined)")

    if macromicro_urls:
        if api_key and fred_series:
            time.sleep(random.uniform(0.5, 1.0))
        print(f"\n[Macromicro Data] Fetching {len(macromicro_urls)} series (limit: {limit} most recent)...")
        macromicro_data = collect_macromicro_data(driver, macromicro_urls, limit)
        all_data.update(macromicro_data)
        if not macromicro_data:
            print("No macromicro data collected")
    else:
        print("\nSkipping macromicro data (no URLs defined)")

    if stooq_urls:
        if macromicro_urls:
            time.sleep(random.uniform(0.5, 1.0))
        print(f"\n[Stooq Data] Fetching {len(stooq_urls)} series (limit: {limit} most recent)...")
        stooq_data = collect_stooq_data(stooq_urls, limit)
        all_data.update(stooq_data)
        if not stooq_data:
            print("No Stooq data collected")
    else:
        print("\nSkipping Stooq data (no URLs defined)")

    if all_data:
        save_to_json(all_data, output_dir, "")

    print("\n" + "=" * 50)
    print("Data collection completed!")
    print(f"Data saved to: {output_dir}")
    print("=" * 50)

    return True
