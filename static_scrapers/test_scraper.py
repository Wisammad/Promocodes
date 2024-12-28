from static_scraper import StaticPromoScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_static_scraper():
    try:
        # Initialize scraper with base URL
        scraper = StaticPromoScraper("https://www.wired.com/coupons")
        logger.info("Starting category and coupon fetch...")
        
        # Fetch all coupons from all categories
        coupons = scraper.fetch_all_coupons()
        
        # Log results
        logger.info(f"Found {len(coupons)} coupons")
        for coupon in coupons:
            logger.info("-------------------")
            logger.info(f"Code: {coupon['code']}")
            logger.info(f"URL: {coupon['url']}")
        
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