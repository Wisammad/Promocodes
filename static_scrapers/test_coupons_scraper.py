from static_scraper_coupons import CouponsComScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coupons_scraper_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_coupons_scraper():
    scraper = None
    try:
        # Initialize scraper
        scraper = CouponsComScraper()
        logger.info("Starting coupon fetch test...")
        
        # Fetch coupons
        coupons = scraper.fetch_coupons()
        
        # Log results
        logger.info("\n=== TEST RESULTS ===")
        logger.info(f"Total coupons found: {len(coupons)}")
        
        if coupons:
            for idx, coupon in enumerate(coupons, 1):
                logger.info("\n-------------------")
                logger.info(f"Coupon {idx}:")
                logger.info(f"Data ID: {coupon.get('data_id', 'N/A')}")
                logger.info(f"Type: {coupon.get('type', 'N/A')}")
                logger.info(f"Title: {coupon.get('title', 'N/A')}")
                
            # Statistics
            types_count = {}
            for coupon in coupons:
                coupon_type = coupon.get('type', 'unknown')
                types_count[coupon_type] = types_count.get(coupon_type, 0) + 1
            
            logger.info("\n=== STATISTICS ===")
            logger.info(f"Total coupons: {len(coupons)}")
            for coupon_type, count in types_count.items():
                logger.info(f"{coupon_type}: {count}")
        else:
            logger.warning("No coupons were found!")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise
    finally:
        if scraper and scraper.driver:
            scraper.driver.quit()
            logger.info("WebDriver closed successfully")

if __name__ == "__main__":
    test_coupons_scraper() 