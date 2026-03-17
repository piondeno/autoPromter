import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from browser.driver import init_driver, close_driver, print_version_info
from automation.gemini import GeminiAutomator
from utils.prompt_reader import list_prompt_files, read_prompts
from utils.data_require_list_reader import list_md_files, parse_md_file, get_output_dir
from data_collector import collect_all_data


def select_prompt_file():
    files = list_prompt_files()

    if not files:
        print("No prompt files found in prompts/ directory.")
        print(f"Please create .txt files in: {config.PROMPTS_DIR}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Select a prompt file:")
    print("=" * 50)

    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")

    while True:
        try:
            choice = input("\nEnter number (1-{}): ".format(len(files))).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)

        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]

        print("Invalid selection. Please try again.")


def select_md_file():
    files = list_md_files()

    if not files:
        print("No MD files found in dataRequireList/ directory.")
        return None

    print("\n" + "=" * 50)
    print("Select a data requirement file:")
    print("=" * 50)

    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    print(f"  {len(files) + 1}. 不下載資料")

    while True:
        try:
            choice = input("\nEnter number (1-{}): ".format(len(files) + 1)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(files) + 1:
            if int(choice) == len(files) + 1:
                return "skip"
            return files[int(choice) - 1]

        print("Invalid selection. Please try again.")


def load_json_data(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def main():
    print_version_info()
    print("Gemini AutoPromter")
    print("-" * 30)

    while True:
        try:
            choice = input("Use existing login session? [y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 'n'

        if choice == 'y':
            force_new = False
            break
        elif choice == 'n':
            force_new = True
            break
        else:
            print("Please enter 'y' or 'n'")

    prompt_file = select_prompt_file()
    print(f"\nSelected: {prompt_file.name}")

    prompts = read_prompts(prompt_file)
    print(f"Loaded {len(prompts)} prompts\n")

    md_file = select_md_file()
    
    driver = None
    json_data_path = None

    if md_file and md_file != "skip":
        print(f"\nSelected: {md_file.name}")
        parsed = parse_md_file(md_file)

        print(f"\nFRED API Key: {'Yes' if parsed['fred_api_key'] else 'No'}")
        print(f"FRED Series: {len(parsed['fred_series'])} items")
        print(f"Macromicro URLs: {len(parsed['macromicro_urls'])} items")
        print(f"Stooq URLs: {len(parsed.get('stooq_urls', []))} items")

        output_dir = get_output_dir(md_file.name)
        print(f"Output directory: {output_dir}")

        print("\nInitializing browser for data collection...")
        driver = init_driver(force_new)

        try:
            collect_all_data(
                api_key=parsed["fred_api_key"],
                fred_series=parsed["fred_series"],
                macromicro_urls=parsed["macromicro_urls"],
                driver=driver,
                output_dir=output_dir,
                limit=config.DATA_KEEP_COUNT,
                stooq_urls=parsed.get("stooq_urls", [])
            )
            json_data_path = output_dir / "data.json"
            if json_data_path.exists():
                print(f"\nJSON file ready: {json_data_path}")
        except Exception as e:
            print(f"Error during data collection: {e}")

        close_driver(driver)
        driver = None

        print("\nData collection completed. Reinitializing browser for Gemini...")
    elif md_file == "skip":
        print("\nNo MD file selected, skipping data download.")

    print("\nInitializing browser...")
    print("Note: Please log in to Gemini if not already logged in.")
    print("The session will be saved for future use.\n")

    if driver is None:
        driver = init_driver(force_new)

    automator = GeminiAutomator(driver)

    try:
        automator.open_gemini()
        input("\nPress Enter after you have logged in...")

        if json_data_path:
            json_file_path = str(json_data_path)
            print(f"\nUploading file: {json_file_path}")
            automator.upload_file_only(json_file_path)
            input("\nPress Enter after confirming file upload...")

            if prompts:
                first_prompt = prompts[0]
                print(f"\nSending first prompt: {first_prompt[:50]}...")
                automator.submit_prompt(first_prompt)
                prompts = prompts[1:]

        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] Ready to send: {prompt[:50]}...")
            while True:
                user_input = input("\n[Enter] or [g] send prompt / [q]uit: ").strip().lower()
                if user_input == "" or user_input == "g":
                    automator.submit_prompt(prompt)
                    break
                elif user_input == "q":
                    print("Quitting...")
                    return
                else:
                    print("Invalid input. Press Enter or 'g' to send, 'q' to quit.")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50)
    print("All prompts completed!")
    print("=" * 50)
    
    while True:
        confirm = input("\nPress [q] to quit and close browser: ").strip().lower()
        if confirm == "q":
            break
    
    print("\nClosing browser...")
    close_driver(driver)
    print("Done.")


if __name__ == "__main__":
    main()
