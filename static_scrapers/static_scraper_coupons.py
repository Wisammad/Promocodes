from static_scraper import StaticPromoScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import time

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CouponsComScraper(StaticPromoScraper):
    def __init__(self, base_url="https://www.coupons.com/top-offers"):
        super().__init__(base_url)

    def parse_expiration_date(self, date_text):
        try:
            date_str = date_text.replace('Expiration date:', '').strip()
            return datetime.strptime(date_str, '%m/%d/%Y')
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_text}': {str(e)}")
            return None

    def fetch_coupons(self):
        try:
            available_codes = []
            logger.info("Starting coupon fetch from coupons.com")
            
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Setup wait
            wait = WebDriverWait(self.driver, 10)
            
            # First find all containers with data-id
            coupon_containers = wait.until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR, 
                    "div[class*='_1ip0fbd5']"
                ))
            )
            logger.info(f"Found {len(coupon_containers)} coupon containers with data-id")
            
            for idx, container in enumerate(coupon_containers, 1):
                try:
                    logger.info(f"\nProcessing coupon {idx}/{len(coupon_containers)}")
                    
                    # Get data attributes from container
                    data_id = container.get_attribute("data-id")
                    data_type = container.get_attribute("data-attribute")
                    logger.info(f"Found data: ID={data_id}, Type={data_type}")
                    
                    # Find the parent container first
                    parent = container.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1ip0fbda')]")
                    
                    # Now find the VoucherCard within this parent using multiple approaches
                    card = None
                    selectors = [
                        ".//div[contains(@class, 'VoucherCard')]",  # XPath approach
                        ".//div[contains(@class, '_17t8r7p0')]",    # Dynamic class approach
                        ".//div[contains(@class, 'hasLogo')]"       # Alternative class
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = parent.find_elements(By.XPATH, selector)
                            if elements:
                                card = elements[0]
                                logger.debug(f"Found card using selector: {selector}")
                                break
                        except Exception:
                            continue
                    
                    if not card:
                        logger.error(f"Could not find VoucherCard for container {idx}")
                        continue
                    
                    # Get shop name - try multiple approaches
                    '''try:
                        shop_elements = card.find_elements(By.CSS_SELECTOR, "a[href*='/coupon-codes']")
                        if shop_elements:
                            shop_name = shop_elements[0].text.strip()
                        else:
                            # Try logo alt text
                            logo_elements = card.find_elements(By.CSS_SELECTOR, "img[alt]")
                            shop_name = logo_elements[0].get_attribute("alt") if logo_elements else None
                        logger.info(f"Shop name: {shop_name}")
                    except Exception as e:
                        logger.warning(f"Could not get shop name: {str(e)}")
                        shop_name = None'''
                    # Get offer title
                    try:
                        title_elements = card.find_elements(By.CSS_SELECTOR, "h3[class*='_17t8r7p8']")
                        if not title_elements:
                            title_elements = card.find_elements(By.TAG_NAME, "h3")
                        title = title_elements[0].text.strip() if title_elements else None
                        logger.info(f"Title: {title}")
                    except Exception as e:
                        logger.warning(f"Could not get title: {str(e)}")
                        title = None
                    
                    if data_id and title:
                        coupon_data = {
                            'data_id': data_id,
                            'type': data_type,
                            'title': title
                        }
                        available_codes.append(coupon_data)
                        logger.info(f"Added coupon: {coupon_data}")
                    
                except Exception as e:
                    logger.error(f"Error processing container {idx}: {str(e)}")
                    continue
            
            # Summary
            logger.info(f"\nScraping Summary:")
            logger.info(f"Total containers found: {len(coupon_containers)}")
            logger.info(f"Successfully processed: {len(available_codes)}")
            if available_codes:
                logger.info("Sample of processed coupons:")
                for code in available_codes[:3]:
                    logger.info(f"- {code}")
            
            return available_codes

        except Exception as e:
            logger.error(f"Fatal error in scraper: {str(e)}")
            return [] 