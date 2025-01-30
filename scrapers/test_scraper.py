from scraper import RetailMeNotScraper
import logging

def test_single_store():
    scraper = RetailMeNotScraper()
    
    # Test with a specific store
    scraper.base_url = "https://www.retailmenot.com/coupons/entertainment"
    
    try:
        results = scraper.scrape_coupons()
        print("\nResults found:")
        for link, coupon in results.items():
            print("\nCoupon Details:")
            print(f"Link: {link}")
            print(f"Company: {coupon.company}")
            print(f"Code: {coupon.code}")
            print(f"Expiration Date: {coupon.expiration_date}")
            print(f"Discount Value: {coupon.discount_value}")
            print("-" * 50)
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_single_store() 