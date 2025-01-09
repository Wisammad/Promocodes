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
            
            # Load initial page with longer wait
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Setup wait
            wait = WebDriverWait(self.driver, 10)
            
            # Find all VoucherCards
            coupon_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.VoucherCard")
            logger.info(f"Found {len(coupon_cards)} VoucherCard elements")
            
            for idx, card in enumerate(coupon_cards, 1):
                try:
                    logger.info(f"\nProcessing coupon {idx}/{len(coupon_cards)}")
                    
                    # Log the card's HTML structure for debugging
                    logger.debug(f"Card HTML structure: {card.get_attribute('outerHTML')}")
                    
                    # Try multiple approaches to find the parent container
                    try:
                        # Approach 1: Direct parent with class
                        parent = card.find_element(By.XPATH, """
                            ./ancestor::div[contains(@class, '_1ip0fbda')]
                            /div[contains(@class, '_1ip0fbd5')]
                        """)
                    except:
                        try:
                            # Approach 2: Search up through known hierarchy
                            parent = card.find_element(By.XPATH, """
                                ./ancestor::div[contains(@class, '_1ip0fbd0')]
                                //div[contains(@class, '_1ip0fbd5')]
                            """)
                        except:
                            # Approach 3: Direct class search
                            parent = self.driver.find_element(
                                By.CSS_SELECTOR, 
                                f"div[class*='_1ip0fbd5'][data-id]"
                            )
                    
                    # Extract data attributes
                    data_id = parent.get_attribute("data-id")
                    data_type = parent.get_attribute("data-attribute")
                    logger.info(f"Found data: ID={data_id}, Type={data_type}")
                    
                    # Get shop name with wait
                    try:
                        shop_element = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                "a[href*='/coupon-codes']"
                            ))
                        )
                        shop_name = shop_element.text.strip()
                        if not shop_name:
                            shop_name = shop_element.get_attribute("title")
                        logger.info(f"Shop name: {shop_name}")
                    except Exception as e:
                        logger.warning(f"Could not get shop name: {str(e)}")
                        shop_name = None
                    
                    # Get offer title with wait
                    try:
                        title_element = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                "h3._17t8r7p8"
                            ))
                        )
                        title = title_element.text.strip()
                        logger.info(f"Title: {title}")
                    except Exception as e:
                        logger.warning(f"Could not get title: {str(e)}")
                        title = None
                    
                    if any([data_id, shop_name, title]):
                        coupon_data = {
                            'data_id': data_id,
                            'type': data_type,
                            'shop_name': shop_name,
                            'title': title
                        }
                        available_codes.append(coupon_data)
                        logger.info(f"Successfully added coupon: {coupon_data}")
                    
                except Exception as e:
                    logger.error(f"Error processing card {idx}: {str(e)}")
                    continue
            
            # Final summary
            logger.info(f"\nScraping Summary:")
            logger.info(f"Total cards found: {len(coupon_cards)}")
            logger.info(f"Successfully processed: {len(available_codes)}")
            
            return available_codes

        except Exception as e:
            logger.error(f"Fatal error in scraper: {str(e)}")
            return [] 