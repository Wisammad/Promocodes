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
            available_codes = []
            
            # Load initial page to get coupon IDs
            self.driver.get(self.base_url)
            time.sleep(2)  # Add small delay for page load
            
            # Get all coupon divs with their data attributes directly
            coupon_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.coupon__logo[data-coupon-id][data-shop-name][data-coupon-title]")
            coupon_data = []
            
            for element in coupon_elements:
                coupon_id = element.get_attribute("data-coupon-id")
                shop_name = element.get_attribute("data-shop-name")
                coupon_title = element.get_attribute("data-coupon-title")
                
                if coupon_id and shop_name and coupon_title:
                    coupon_data.append({
                        "id": coupon_id,
                        "shop_name": shop_name,
                        "title": coupon_title
                    })

            # Remove duplicates while preserving order
            seen_ids = set()
            unique_coupons = []
            for coupon in coupon_data:
                if coupon["id"] not in seen_ids:
                    seen_ids.add(coupon["id"])
                    unique_coupons.append(coupon)

            print(f"\nFound {len(unique_coupons)} unique coupons")

            # Print found IDs
            print("\n=== FOUND COUPONS ===")
            for idx, coupon in enumerate(unique_coupons, 1):
                print(f"ID {idx}: {coupon['id']}")
                if coupon['shop_name']: print(f"Shop: {coupon['shop_name']}")
                if coupon['title']: print(f"Title: {coupon['title']}")
                print("------------------------")
            print(f"Total coupons found: {len(unique_coupons)}")
            print("========================\n")

            for idx, coupon in enumerate(unique_coupons, 1):
                try:
                    coupon_url = f"{self.base_url}#id-{coupon['id']}"
                    print(f"Processing {idx}/{len(unique_coupons)}: {coupon['id']}")
                    if coupon['shop_name']: print(f"Shop: {coupon['shop_name']}")
                    if coupon['title']: print(f"Title: {coupon['title']}")
                    
                    self.driver.get(coupon_url)
                    self.driver.refresh()

                    modal_exists = len(self.driver.find_elements(By.CSS_SELECTOR, 'div.modal[id="my-modal"][data-area="MOD"]')) > 0
                    
                    if modal_exists:
                        modal = self.driver.find_element(By.CSS_SELECTOR, 'div.modal[id="my-modal"][data-area="MOD"]')
                        no_code_elements = modal.find_elements(By.CSS_SELECTOR, 'span.modal-clickout__code--empty')
                        
                        if not no_code_elements:
                            code = modal.find_element(By.CLASS_NAME, "modal-clickout__code").text
                            available_codes.append({
                                "code": code,
                                "url": coupon_url,
                                "shop_name": coupon['shop_name'],
                                "title": coupon['title']
                            })
                            print(f"✓ Found valid code: {code}")
                        else:
                            print("✗ No code required")

                except Exception as e:
                    print(f"✗ Error processing coupon: {str(e)}")
                    continue

            # Print final results
            print("\n=== AVAILABLE PROMO CODES ===")
            for item in available_codes:
                if item['shop_name']: print(f"Shop: {item['shop_name']}")
                if item['title']: print(f"Title: {item['title']}")
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

    def fetch_category_urls(self):
        try:
            print("\n=== Starting Category URL Fetch ===")
            url = f"{self.base_url}/categories/"
            print(f"Accessing URL: {url}")
            self.driver.get(url)
            
            print("\nWaiting for elements to load...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.categories__list"))
                )
                print("✓ Elements loaded successfully")
            except Exception as wait_error:
                print(f"⚠️ Timeout waiting for elements: {str(wait_error)}")
            
            category_urls = set()
            
            print("\n=== Checking Category Links ===")
            content_links = self.driver.find_elements(By.CSS_SELECTOR, "ul.categories__list a.categories__link")
            print(f"Found {len(content_links)} category links")
            
            for link in content_links:
                try:
                    href = link.get_attribute("href")
                    name_element = link.find_elements(By.CSS_SELECTOR, "span.categories__name")
                    text = name_element[0].text.strip() if name_element else link.text.strip()
                    
                    if href and "coupons/categories" in href:
                        category_urls.add(href)
                except Exception as e:
                    print(f"⚠️ Error processing category link: {str(e)}")
            
            # If no categories found, try alternative approach
            if not category_urls:
                print("\n=== Trying Alternative Approach ===")
                print("Looking for any category-related links...")
                
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"\nTotal links found on page: {len(all_links)}")
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        if href and "coupons/categories" in href:
                            category_urls.add(href)
                    except Exception as e:
                        continue
            
            # Final results
            category_urls = list(category_urls)
            print("\n=== FINAL RESULTS ===")
            print(f"Total unique category URLs found: {len(category_urls)}")
            for idx, url in enumerate(category_urls, 1):
                print(f"Category {idx}: {url}")
            
            # Save debug info if no URLs found
            if not category_urls:
                print("\n⚠️ No category URLs found!")
                print("Saving page source and screenshots...")
                self.save_page_source("no_categories_found.html", self.driver.page_source)
                self.driver.save_screenshot("debug_screenshot.png")
                
                # Log all links found on the page
                print("\n=== All Links on Page ===")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for idx, link in enumerate(all_links, 1):
                    try:
                        print(f"\nLink {idx}:")
                        print(f"- HTML: {link.get_attribute('outerHTML')}")
                        print(f"- HREF: {link.get_attribute('href')}")
                        print(f"- Text: {link.text.strip()}")
                    except:
                        continue
            
            return category_urls

        except Exception as e:
            print(f"❌ Critical error finding category URLs: {str(e)}")
            self.save_page_source("critical_error.html", self.driver.page_source)
            self.driver.save_screenshot("error_screenshot.png")
            return []

    def fetch_all_coupons(self):
        all_coupons = []
        
        # First get all category URLs
        category_urls = self.fetch_category_urls()
        
        # Process each category
        for idx, category_url in enumerate(category_urls, 1):
            print(f"\nProcessing category {idx}/{len(category_urls)}")
            print(f"URL: {category_url}")
            
            # Temporarily update base_url for this category
            original_base_url = self.base_url
            self.base_url = category_url
            
            # Use existing fetch_coupons logic
            category_coupons = self.fetch_coupons()
            all_coupons.extend(category_coupons)
            
            # Restore original base_url
            self.base_url = original_base_url
        
        # Print final summary
        print("\n=== FINAL RESULTS ===")
        print(f"Total categories processed: {len(category_urls)}")
        print(f"Total coupons found: {len(all_coupons)}")
        print("===================\n")
        
        return all_coupons