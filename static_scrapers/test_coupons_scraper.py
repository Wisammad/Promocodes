from static_scraper_coupons import CouponsComScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coupons_scraper():
    try:
        # Initialize scraper
        scraper = CouponsComScraper()
        logger.info("Starting coupon fetch...")
        
        # Fetch coupons
        coupons = scraper.fetch_coupons()
        
        # Log results
        logger.info(f"Found {len(coupons)} coupons")
        for coupon in coupons:
            logger.info("-------------------")
            logger.info(f"Shop: {coupon['shop_name']}")
            logger.info(f"Title: {coupon['title']}")
            logger.info(f"URL: {coupon['url']}")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
    finally:
        scraper.driver.quit()

if __name__ == "__main__":
    test_coupons_scraper() 