from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import logging
import time
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticPromoScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.setup_selenium()
        self.processed_codes = set()

    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.implicitly_wait(10)

    def scroll_to_load_more(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        retries = 0
        max_retries = 5

        while retries < max_retries:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load

            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                retries += 1
            else:
                retries = 0
                last_height = new_height
                logger.info("Scrolled to load more content...")

    def save_page_source(self, filename, source):
        """Helper method to save page source"""
        try:
            with open(f"debug_pages/{filename}", "w", encoding='utf-8') as f:
                f.write(source)
            logger.info(f"Saved page source to debug_pages/{filename}")
        except Exception as e:
            logger.error(f"Failed to save page source: {str(e)}")

    def fetch_coupons(self):
        try:
            available_codes = []  # List to store valid codes and their URLs
            
            # Load initial page to get coupon IDs
            self.driver.get(self.base_url)
            coupon_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-coupon-id]")
            coupon_ids = list({element.get_attribute("data-coupon-id") for element in coupon_elements})

            # Print found IDs
            print("\n=== FOUND COUPON IDs ===")
            for idx, coupon_id in enumerate(coupon_ids, 1):
                print(f"ID {idx}: {coupon_id}")
            print(f"Total IDs found: {len(coupon_ids)}")
            print("========================\n")

            for idx, coupon_id in enumerate(coupon_ids, 1):
                try:
                    coupon_url = f"{self.base_url}#id-{coupon_id}"
                    print(f"Trying ID {idx}/{len(coupon_ids)}: {coupon_id}")
                    
                    self.driver.get(coupon_url)
                    self.driver.refresh()

                    modal_exists = len(self.driver.find_elements(By.CSS_SELECTOR, 'div.modal[id="my-modal"][data-area="MOD"]')) > 0
                    
                    if modal_exists:
                        modal = self.driver.find_element(By.CSS_SELECTOR, 'div.modal[id="my-modal"][data-area="MOD"]')
                        
                        # Check for "code not required" case
                        no_code_elements = modal.find_elements(By.CSS_SELECTOR, 'span.modal-clickout__code--empty')
                        if not no_code_elements:  # If it's a valid code
                            code = modal.find_element(By.CLASS_NAME, "modal-clickout__code").text
                            available_codes.append({
                                "code": code,
                                "url": coupon_url
                            })
                            print(f"✓ Found valid code for ID {coupon_id}")
                        else:
                            print(f"✗ No code required for ID {coupon_id}")

                except Exception as e:
                    print(f"✗ Error processing ID {coupon_id}: {str(e)}")
                    continue

            # Print final results
            print("\n=== AVAILABLE PROMO CODES ===")
            for item in available_codes:
                print(f"Code: {item['code']}")
                print(f"URL: {item['url']}")
                print("----------------------------")
            print(f"Total codes found: {len(available_codes)}")
            print("============================\n")

            return available_codes

        except Exception as e:
            print(f"Error in scraper: {str(e)}")
            return []

    def determine_discount_type(self, text):
        return "percentage" if "%" in text else "fixed"

    def extract_discount_value(self, text):
        if text:
            value = ''.join(filter(str.isdigit, text))
            try:
                return float(value)
            except ValueError:
                return 0.00
        return 0.00

    def parse_expiration_date(self, date_text):
        if date_text:
            try:
                return datetime.strptime(date_text.strip(), "%m/%d/%Y")
            except ValueError:
                pass
        return datetime.utcnow() + timedelta(days=30)

    def is_duplicate(self, code):
        return code in self.processed_codes

    def mark_as_processed(self, code):
        self.processed_codes.add(code)

    def save_to_api(self, promo_codes):
        # Reference the save_to_api implementation from pipelines.py
        # Reference lines 4-34 from pipelines.py
        pass