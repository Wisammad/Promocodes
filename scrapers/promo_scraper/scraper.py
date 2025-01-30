import logging
import random
import time
import ast
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from urllib.parse import urlparse, parse_qs

from fake_useragent import UserAgent
from retry import retry

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException, 
    NoSuchElementException
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Coupon:
    """
    Data container for a single coupon.
    """
    code: str
    expiration_date: Optional[datetime]
    discount_value: Optional[str]
    company: Optional[str]
    url: str

class RetailMeNotScraper:
    """
    Scraper for RetailMeNot's Entertainment Coupons.
    1. Loads all offers by repeatedly clicking 'Show More'.
    2. Finds coupon links for 'Coupon code' offers.
    3. Extracts coupon details from each offer page.
    """

    def __init__(self):
        self.user_agent = UserAgent()
        self.base_url = "https://www.retailmenot.com/"
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        Set up and return a Chrome WebDriver with custom options.
        """
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.user_agent.random}')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)  # Timeout for page loads
        return driver

    def load_all_offers(self, driver: webdriver.Chrome) -> bool:
        """
        Navigate to the Entertainment coupons page and recursively load all offers 
        by clicking 'Show More' until no more offers are loaded or no button is found.
        """
        logger.info("=== Load All Offers Process ===")
        try:
            logger.info("Navigating to entertainment coupons page...")
            driver.get("https://www.retailmenot.com/coupons/entertainment")
            
            # Wait for the page to fully load
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.info("Page fully loaded.")
                        
            # Wait for at least one offer to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(@href, '/out/O/')]")
                    )
                )
            except TimeoutException:
                logger.warning("No offers found within 10 seconds.")
                return False
            
            # Get initial count of offers
            initial_offers = len(
                driver.find_elements(By.XPATH, "//a[contains(@href, '/out/O/')]")
            )
            logger.info(f"Initial number of offers: {initial_offers}")
            
            # Repeatedly click "Show More" until no new offers load
            while True:
                try:
                    show_more = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            "//button[contains(@class, 'w-48') and contains(@class, 'bg-purple-700')]"
                        ))
                    )
                    logger.info("Found 'Show More' button. Attempting to click...")
                    
                    # Scroll the button into view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", 
                        show_more
                    )
                    time.sleep(1.5)
                    
                    # Try regular click first; fallback to JS if needed
                    try:
                        show_more.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", show_more)
                    
                    logger.info("Clicked 'Show More' button. Waiting for new offers...")
                    time.sleep(0.5) #change this if you want to wait longer for the next 'show more' button to be clicked
                    
                    # Check if new offers have loaded
                    current_offers = len(
                        driver.find_elements(By.XPATH, "//a[contains(@href, '/out/O/')]")
                    )
                    logger.info(f"Current number of offers: {current_offers}")
                    
                    # If no new offers loaded, stop
                    if current_offers <= initial_offers:
                        logger.info("No new offers loaded, stopping.")
                        break
                    initial_offers = current_offers
                    
                except TimeoutException:
                    logger.info("No more 'Show More' buttons found.")
                    break
        
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user.")
            return True
        
        except Exception as e:
            logger.error(f"An error occurred while loading offers: {str(e)}")
            return False
        
        return True

    def find_coupon_links(self, driver: webdriver.Chrome) -> List[str]:
        """
        Find and return all coupon links from the currently loaded Entertainment coupons page.
        Only returns links that indicate a 'Coupon code'.
        """
        try:
            wait = WebDriverWait(driver, 10)
            
            # Attempt to close Google Sign-in if present
            try:
                iframe = driver.find_element(By.ID, "credential_picker_iframe")
                if iframe:
                    driver.execute_script(
                        "document.getElementById('credential_picker_container').remove();"
                    )
                    time.sleep(1)
            except Exception:
                pass

            # Wait until at least one coupon link is present
            coupon_elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@href, '/out/O/')]")
                )
            )
            logger.info(f"Found {len(coupon_elements)} total offers (deals/coupons/etc.).")
            
            links = []
            for element in coupon_elements:
                try:
                    # Ensure it's labeled as "Coupon code"
                    if not element.find_elements(By.XPATH, ".//p[text()='Coupon code']"):
                        continue
                    
                    href = element.get_attribute('href')
                    x_data = element.get_attribute('x-data')
                    
                    if href and x_data and 'outclickHandler' in x_data:
                        # Parse the x-data attribute
                        x_data_str = x_data.replace("outclickHandler(", "").replace(")", "")
                        x_data_dict = ast.literal_eval(x_data_str)
                        
                        offer_uuid = x_data_dict.get("offerUuid")
                        site_link = x_data_dict.get("siteLink")
                        
                        if offer_uuid and site_link:
                            view_url = f"https://www.retailmenot.com/view/{offer_uuid}{site_link}"
                            logger.info(f"Found coupon URL: {view_url}")
                            links.append(view_url)
                            
                except Exception as e:
                    logger.error(f"Error processing coupon element: {str(e)}")
                    continue
            
            return links
            
        except Exception as e:
            logger.error(f"Error finding coupon links: {str(e)}")
            return []

    def extract_code_from_page(self, driver: webdriver.Chrome, url: str) -> Optional[Coupon]:
        """
        Extract coupon code and additional information from a specific coupon page.
        """
        try:
            wait = WebDriverWait(driver, 10)
            
            # Discount value (e.g., "10% Off" or "Save $5") 
            try:
                discount_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//h2[contains(@class, 'mb-2') and contains(@class, 'text-center') "
                        "and contains(@class, 'font-bold')]"
                    ))
                )
                discount_value = discount_element.text.strip()
            except Exception as e:
                logger.warning(f"Could not extract discount value: {e}")
                return None
            
            # Expiration date
            try:
                date_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//p[contains(@class, 'font-semibold') and contains(text(), 'Ends')]"
                    ))
                )
                date_text = date_element.text.replace('Ends ', '').strip()
                expiration_date = datetime.strptime(date_text, '%m/%d/%Y')
            except Exception as e:
                logger.warning(f"Could not extract expiration date: {e}")
                expiration_date = None
            
            # Coupon code (if present)
            try:
                code_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[contains(@class, 'relative') and contains(@class, 'mx-auto')][@x-data='codeGenerator()']"
                    ))
                )
                code = code_element.text.split('COPY')[0].strip()
            except Exception:
                code = ""  # If no code found, use empty string
            
            # Company name
            try:
                company_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//a[@rel='nofollow sponsored' and contains(@class, 'text-purple-700')]"
                    ))
                )
                company = company_element.text.strip()
            except Exception as e:
                logger.warning(f"Could not extract company name: {e}")
                company = None
            
            coupon = Coupon(
                code=code,
                expiration_date=expiration_date,
                discount_value=discount_value,
                company=company,
                url=url
            )
            logger.info(f"Extracted coupon: {coupon}")
            return coupon
            
        except Exception as e:
            logger.error(f"Error extracting coupon info from {url}: {str(e)}")
            driver.save_screenshot(f"error_{int(time.time())}.png")
            return None

    @retry(TimeoutException, tries=3, delay=2, backoff=2)
    def scrape_coupons(self) -> Dict[str, Coupon]:
        """
        Main scraping workflow:
        1. Set up the driver.
        2. Load all offers recursively.
        3. Find coupon links (Coupon code only).
        4. Extract coupon details for each link.
        5. Return dictionary of results.
        """
        driver = None
        try:
            logger.info("Starting coupon scrape...")
            driver = self.setup_driver()
            
            # Ensure all offers are loaded
            self.load_all_offers(driver)
            
            # Gather all coupon links
            coupon_links = self.find_coupon_links(driver)
            logger.info(f"Found {len(coupon_links)} coupon links labeled 'Coupon code'")
            
            results = {}
            processed_urls = set()
            
            # Visit each coupon link and extract data
            for link in coupon_links:
                if link in processed_urls:
                    logger.info(f"Skipping duplicate link: {link}")
                    continue
                
                processed_urls.add(link)
                driver.get(link)
                time.sleep(random.uniform(2, 4))  # Slight pause between page loads
                
                coupon = self.extract_code_from_page(driver, link)
                if coupon:
                    results[link] = coupon
            
            return results
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return {}
        finally:
            if driver:
                driver.quit()

def main():
    scraper = RetailMeNotScraper()
    results = scraper.scrape_coupons()
    
    logger.info("Scraping completed. Results:")
    for link, coupon in results.items():
        print(f"Link: {link}")
        print(f"Code: {coupon.code}")
        print(f"Expiration Date: {coupon.expiration_date}")
        print(f"Discount Value: {coupon.discount_value}")
        print(f"Company: {coupon.company}")
        print("-" * 50)

if __name__ == "__main__":
    main()
