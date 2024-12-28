from static_scraper import StaticPromoScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_static_scraper():
    try:
        # Initialize scraper with base URL
        scraper = StaticPromoScraper("https://www.wired.com/coupons/categories/department-stores")
        logger.info("Starting coupon fetch...")
        
        # Fetch all coupons
        coupons = scraper.fetch_coupons()
        
        # Log results
        logger.info(f"Found {len(coupons)} coupons")
        for coupon in coupons:
            logger.info("-------------------")
            logger.info(f"Code: {coupon['code']}")
            logger.info(f"Platform: {coupon['platform']}")
            logger.info(f"Discount Type: {coupon['discount_type']}")
            logger.info(f"Discount Value: {coupon['discount_value']}")
            logger.info(f"Expiration Date: {coupon['expiration_date']}")
        
        # Save to API if coupons were found
        if coupons:
            logger.info("Attempting to save to API...")
            scraper.save_to_api(coupons)
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
    finally:
        scraper.driver.quit()

if __name__ == "__main__":
    test_static_scraper()