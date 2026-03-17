import time
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config


class GeminiAutomator:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.TIMEOUT)

    def open_gemini(self):
        self.driver.get(config.GEMINI_URL)
        time.sleep(2)

    def find_input_box(self):
        selectors = [
            'div[aria-label="請輸入 Gemini 提示詞"]',
            'div.ql-editor',
            'div[contenteditable="true"][role="textbox"]',
            'textarea[aria-label*="Message"]',
            'textarea[aria-label*="提示"]',
        ]

        print("Searching for input box...", end=" ", flush=True)
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                print(f"Found: {selector}")
                return element
            except NoSuchElementException:
                print(".", end="", flush=True)
                continue

        raise NoSuchElementException("Could not find Gemini input box")

    def type_slowly(self, element, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(config.INPUT_DELAY_MIN, config.INPUT_DELAY_MAX))

    def submit_prompt(self, prompt: str):
        input_box = self.find_input_box()
        input_box.click()
        time.sleep(0.5)

        input_box.send_keys(prompt)
        time.sleep(0.5)

        input_box.send_keys(Keys.RETURN)
        print(f"Submitted prompt: {prompt[:50]}...")

    def upload_file_only(self, file_path: str):
        input_box = self.find_input_box()
        input_box.click()
        time.sleep(0.5)

        add_button_selectors = [
            'button[mat-icon-button][aria-label*="add"]',
            'button mat-icon[fonticon="add_2"]',
            'mat-icon[fonticon="add_2"]',
            'button[aria-label*="新增"]',
            'button[aria-label*="Add"]',
        ]

        add_button = None
        for selector in add_button_selectors:
            try:
                add_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if add_button:
                    print(f"Found add button: {selector}")
                    break
            except:
                continue

        if add_button:
            add_button.click()
            time.sleep(1)

            upload_menu_selectors = [
                'div.menu-text:contains("上傳檔案")',
                'div[class="menu-text"]',
                'div:contains("上傳檔案")',
            ]

            upload_menu = None
            for selector in upload_menu_selectors:
                try:
                    if ':contains' in selector:
                        upload_menu = self.driver.find_element(By.CSS_SELECTOR, selector.replace(':contains("上傳檔案")', ''))
                        if upload_menu and '上傳檔案' in upload_menu.text:
                            print(f"Found upload menu: {selector}")
                            break
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if '上傳檔案' in elem.text or 'upload' in elem.text.lower():
                                upload_menu = elem
                                print(f"Found upload menu: {selector}")
                                break
                        if upload_menu:
                            break
                except:
                    continue

            if upload_menu:
                upload_menu.click()
                time.sleep(1)

            file_input_selectors = [
                'input[type="file"]',
                'input[type="upload"]',
            ]

            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if file_input:
                        print(f"Found file input: {selector}")
                        break
                except:
                    continue

            if file_input:
                file_input.send_keys(file_path)
                print(f"Uploaded file: {file_path}")
                time.sleep(2)

        print("File uploaded, waiting for confirmation...")

    def submit_prompt_with_file_upload(self, prompt: str, file_path: str):
        input_box = self.find_input_box()
        input_box.click()
        time.sleep(0.5)

        upload_button_selectors = [
            'button[aria-label="上傳檔案"]',
            'button[aria-label="Upload file"]',
            'button[aria-label*="上傳"]',
            'button[mat-icon-button][aria-label*="add"]',
            'button mat-icon[fonticon="add_2"]',
            'mat-icon[fonticon="add_2"]',
        ]

        upload_button = None
        for selector in upload_button_selectors:
            try:
                upload_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if upload_button:
                    print(f"Found upload button: {selector}")
                    break
            except:
                continue

        if upload_button:
            upload_button.click()
            time.sleep(1)

            file_input_selectors = [
                'input[type="file"]',
                'input[type="upload"]',
            ]

            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if file_input:
                        print(f"Found file input: {selector}")
                        break
                except:
                    continue

            if file_input:
                file_input.send_keys(file_path)
                print(f"Uploaded file: {file_path}")
                time.sleep(2)

        time.sleep(0.5)

        input_box = self.find_input_box()
        input_box.click()
        time.sleep(0.5)

        input_box.send_keys(prompt)
        time.sleep(0.3)

        input_box.send_keys(Keys.RETURN)
        print(f"Submitted prompt with file upload: {prompt[:50]}...")

    def wait_for_response(self, timeout: int = 60) -> bool:
        try:
            stop_button_selectors = [
                'button[aria-label="Stop"]',
                'button[aria-label="停止"]',
                'button.stop-button',
            ]

            for selector in stop_button_selectors:
                try:
                    stop_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if stop_button.is_displayed():
                        print("Waiting for response generation to complete...")
                        WebDriverWait(self.driver, timeout).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        time.sleep(config.AFTER_SUBMIT_DELAY)
                        return True
                except:
                    continue

            time.sleep(config.AFTER_SUBMIT_DELAY)
            return True

        except TimeoutException:
            print("Timeout waiting for response")
            return False

    def is_blocked(self) -> bool:
        blocked_indicators = [
            "Access denied",
            "blocked",
            "captcha",
            "reCAPTCHA",
            "verify you are human",
        ]

        page_source = self.driver.page_source.lower()
        return any(indicator in page_source for indicator in blocked_indicators)
