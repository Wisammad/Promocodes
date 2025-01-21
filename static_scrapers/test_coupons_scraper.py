import logging
from static_scraper_coupons import CouponsComScraper
import os
import time

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_html_to_file(html_content, data_id):
    # Create 'debug_pages' directory if it doesn't exist
    if not os.path.exists('debug_pages'):
        os.makedirs('debug_pages')
    
    # Save HTML to file
    filename = f'debug_pages/voucher_{data_id}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"Saved HTML content to {filename}")

def test_button_details():
    """Test finding SEE COUPON buttons and their details"""
    with CouponsComScraper() as scraper:
        logger.info("Testing button details...")
        
        # Wait for page load
        scraper.page.goto(scraper.base_url)
        time.sleep(5)
        
        # Find buttons with specific class pattern
        buttons = scraper.page.evaluate("""
            () => {
                const buttons = [];
                document.querySelectorAll('div[role="button"]').forEach(btn => {
                    if (btn.textContent.includes('See coupon')) {
                        const container = btn.closest('div[data-id]');
                        buttons.push({
                            text: btn.textContent,
                            classes: btn.className,
                            containerId: container ? container.getAttribute('data-id') : null,
                            containerType: container ? container.getAttribute('data-attribute') : null,
                            isVisible: btn.offsetParent !== null,
                            rect: btn.getBoundingClientRect()
                        });
                    }
                });
                return buttons;
            }
        """)
        
        logger.info(f"Found {len(buttons)} SEE COUPON buttons")
        for idx, button in enumerate(buttons, 1):
            logger.info(f"\nButton {idx}:")
            logger.info(f"Text: {button['text']}")
            logger.info(f"Classes: {button['classes']}")
            logger.info(f"Container ID: {button['containerId']}")
            logger.info(f"Container Type: {button['containerType']}")
            logger.info(f"Is Visible: {button['isVisible']}")
            logger.info(f"Position: {button['rect']}")
        
        return buttons

def test_coupon_scraper():
    """Test the main coupon scraping functionality"""
    scraper = None
    try:
        scraper = CouponsComScraper()
        coupons = scraper.fetch_coupons()
        
        # Log summary
        logger.info("\nScraping Results:")
        logger.info(f"Total coupon codes found: {len(coupons)}")
        
        # Log details of each coupon
        for idx, coupon in enumerate(coupons, 1):
            logger.info(f"\nCoupon Code {idx}:")
            logger.info(f"  Shop: {coupon.get('shop_name', 'Unknown')}")
            logger.info(f"  Title: {coupon.get('title', 'Unknown')}")
            logger.info(f"  Code: {coupon.get('code', 'No code found')}")
        
        return coupons
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return []
    finally:
        if scraper:
            try:
                scraper.cleanup()
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")

def main():
    logger.info("Starting coupon button test...")
    
    try:
        buttons = test_button_details()
        logger.info(f"\nSummary:")
        logger.info(f"Total SEE COUPON buttons found: {len(buttons)}")
        logger.info(f"Visible buttons: {sum(1 for b in buttons if b['isVisible'])}")
        logger.info(f"Buttons in 'code' containers: {sum(1 for b in buttons if b['containerType'] == 'code')}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_coupon_scraper() 