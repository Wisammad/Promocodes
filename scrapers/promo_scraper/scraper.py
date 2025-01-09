from urllib.parse import urlparse, parse_qs
import logging
import random
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from fake_useragent import UserAgent
from retry import retry
from webdriver_manager.chrome import ChromeDriverManager
import ast
from dataclasses import dataclass
from datetime import datetime

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
    code: str
    expiration_date: Optional[datetime]
    discount_value: Optional[str]
    company: Optional[str]
    url: str

class RetailMeNotScraper:
    def __init__(self):
        self.user_agent = UserAgent()
        self.base_url = "https://www.retailmenot.com/"
        
    def setup_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.user_agent.random}')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)  # Add timeout for page loads
        return driver

    def find_coupon_links(self, driver: webdriver.Chrome) -> List[str]:
        """Find all coupon links on the entertainment coupons page"""
        try:
            wait = WebDriverWait(driver, 10)
            
            # Navigate to entertainment section
            driver.get("https://www.retailmenot.com/coupons/entertainment")
            time.sleep(2)
            
            # Try to close Google Sign-in if present
            try:
                iframe = driver.find_element(By.ID, "credential_picker_iframe")
                if iframe:
                    driver.execute_script("""
                        var element = document.getElementById('credential_picker_container');
                        if(element) element.remove();
                    """)
                    time.sleep(1)
            except Exception:
                pass

            # Look for coupon links with href containing '/out/O/'
            coupon_elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@href, '/out/O/')]")
                )
            )
            
            print(f"Found {len(coupon_elements)} coupon elements")
            
            links = []
            for element in coupon_elements:
                try:
                    # Get both href and x-data attributes
                    href = element.get_attribute('href')
                    x_data = element.get_attribute('x-data')
                    
                    if href and x_data and 'outclickHandler' in x_data:
                        # Parse x-data to get offerUuid
                        x_data_str = x_data.replace("outclickHandler(", "").replace(")", "")
                        x_data_dict = ast.literal_eval(x_data_str)
                        
                        offer_uuid = x_data_dict.get("offerUuid")
                        site_link = x_data_dict.get("siteLink")
                        
                        if offer_uuid and site_link:
                            # Construct the view URL
                            view_url = f"https://www.retailmenot.com/view/{offer_uuid}{site_link}"
                            print(f"Found coupon URL: {view_url}")
                            links.append(view_url)
                            
                except Exception as e:
                    print(f"Error processing element: {str(e)}")
                    continue
            
            return links
            
        except Exception as e:
            logger.error(f"Error finding coupon links: {str(e)}")
            return []

    def extract_code_from_page(self, driver: webdriver.Chrome, url: str) -> Optional[Coupon]:
        """Extract coupon code and additional information from the page"""
        try:
            wait = WebDriverWait(driver, 10)
            
            # Get discount value first (this should always be present)
            try:
                discount_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//h2[contains(@class, 'mb-2') and contains(@class, 'text-center') and contains(@class, 'font-bold')]"
                    ))
                )
                discount_value = discount_element.text.strip()
            except Exception as e:
                logger.warning(f"Could not extract discount value: {e}")
                return None
            
            # Get expiration date
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
            
            # Try to get code if it exists
            try:
                code_element = wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//div[contains(@class, 'relative') and contains(@class, 'mx-auto')][@x-data='codeGenerator()']"
                    ))
                )
                code = code_element.text.split('COPY')[0].strip()
            except Exception:
                # If no code found, set code to empty string
                code = ""
            
            # Get company name
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
            
            # Create and return Coupon object
            coupon = Coupon(
                code=code,
                expiration_date=expiration_date,
                discount_value=discount_value,
                company=company,
                url=url
            )
            
            logger.info(f"Found coupon: {coupon}")
            return coupon
            
        except Exception as e:
            logger.error(f"Error extracting coupon info: {str(e)}")
            driver.save_screenshot(f"error_{int(time.time())}.png")
            return None

    @retry(TimeoutException, tries=3, delay=2, backoff=2)
    def scrape_coupons(self) -> Dict[str, Coupon]:
        driver = None
        try:
            logger.info("Starting coupon scrape")
            driver = self.setup_driver()
            
            # Get coupon links
            coupon_links = self.find_coupon_links(driver)
            logger.info(f"Found {len(coupon_links)} coupon links")
            
            # Use a set to track processed URLs
            processed_urls = set()
            
            # Extract coupon information from each link
            results = {}
            for link in coupon_links:
                try:
                    # Skip if we've already processed this URL
                    if link in processed_urls:
                        logger.info(f"Skipping duplicate URL: {link}")
                        continue
                        
                    processed_urls.add(link)
                    driver.get(link)
                    time.sleep(random.uniform(2, 4))
                    
                    coupon = self.extract_code_from_page(driver, link)
                    if coupon:
                        results[link] = coupon
                        logger.info(f"Found coupon: {coupon}")
                    
                except Exception as e:
                    logger.error(f"Error processing link {link}: {str(e)}")
                    continue
            
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
    
    logger.info("Scraping completed")
    for link, coupon in results.items():
        print(f"Link: {link}")
        print(f"Code: {coupon.code}")
        print(f"Expiration Date: {coupon.expiration_date}")
        print(f"Discount Value: {coupon.discount_value}")
        print("-" * 50)

if __name__ == "__main__":
    main() 