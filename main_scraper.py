from static_scrapers.static_scraper import StaticPromoScraper
from scrapers.promo_scraper.scraper import RetailMeNotScraper
from models import PromoCode, MerchantRevenue
from database import db
from app import app
from datetime import datetime
import logging
import re
from dataclasses import asdict
from sqlalchemy import inspect
from sqlalchemy.sql import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_discount_value(value_str):
    """Extract numeric value and determine discount type from string."""
    if not value_str:
        return 0.00, "unknown"
    
    # Convert to string if not already
    value_str = str(value_str)
    
    # Handle RetailMeNot specific formats
    if "Off" in value_str:
        # Extract percentage
        percent_match = re.search(r'(\d+)%\s+Off', value_str)
        if percent_match:
            return float(percent_match.group(1)), "percentage"
        
        # Extract dollar amount
        dollar_match = re.search(r'\$(\d+(?:\.\d{2})?)\s+Off', value_str)
        if dollar_match:
            return float(dollar_match.group(1)), "fixed"
    
    # Handle Wired specific formats
    percent_match = re.search(r'(\d+)%', value_str)
    if percent_match:
        return float(percent_match.group(1)), "percentage"
    
    dollar_match = re.search(r'\$(\d+(?:\.\d{2})?)', value_str)
    if dollar_match:
        return float(dollar_match.group(1)), "fixed"
    
    return 0.00, "other"

def parse_expiration_date(date_str):
    """Parse expiration date string to datetime object."""
    try:
        if isinstance(date_str, datetime):
            return date_str
        if not date_str or str(date_str).lower() in ['soon', 'ongoing']:
            return datetime(2025, 12, 31)  # Default expiration
        
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y']:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
                
        return datetime(2025, 12, 31)  # Default if no format matches
        
    except (ValueError, AttributeError):
        return datetime(2025, 12, 31)  # Default expiration

def format_retailmenot_coupon(coupon):
    """Convert RetailMeNot Coupon object to dictionary format."""
    if hasattr(coupon, '__dict__'):
        return {
            'code': coupon.code,
            'discount_value': coupon.discount_value,
            'company': coupon.company,
            'expiration_date': coupon.expiration_date,
            'url': coupon.url
        }
    return None

def format_wired_coupon(coupon):
    """Convert Wired coupon data to consistent format."""
    return {
        'code': coupon.get('code', ''),
        'discount_value': coupon.get('title', ''),
        'company': coupon.get('shop_name', ''),
        'expiration_date': None,  # Wired doesn't provide expiration dates
        'url': coupon.get('url', '')
    }

def insert_promo_code(coupon_data, platform):
    """Insert promo code into database."""
    try:
        if platform == 'RetailMeNot':
            coupon_data = format_retailmenot_coupon(coupon_data)
        else:
            coupon_data = format_wired_coupon(coupon_data)
            
        if not coupon_data:
            logger.debug("Invalid coupon data format")
            return False

        code = coupon_data['code'].strip().upper()
        if not code or code.lower().startswith(('sent', 'code sent')):
            logger.debug(f"Skipping invalid code: {code}")
            return False
            
        with app.app_context():
            try:
                # Check for existing code using SQLAlchemy
                existing_code = PromoCode.query.filter(
                    func.upper(PromoCode.code) == code
                ).first()

                if existing_code:
                    logger.debug(f"Found existing code in DB: '{existing_code.code}' vs new code: '{code}'")
                    return False

                # Get discount details
                discount_amount, discount_type = parse_discount_value(coupon_data['discount_value'])
                
                # Create promo code record
                promo_code = PromoCode(
                    code=code,
                    platform=platform,
                    discount_type=discount_type,
                    discount_value=discount_amount,
                    expiration_date=parse_expiration_date(coupon_data.get('expiration_date')),
                    usage_limit=100,
                    revenue_share=5.00,
                    user_profile_restriction={},
                    location_restriction={}
                )
                
                db.session.add(promo_code)
                db.session.flush()
                
                merchant_revenue = MerchantRevenue(
                    merchant_name=coupon_data['company'] or 'Unknown Merchant',
                    promo_code=promo_code,
                    revenue_generated=0.00,
                    company_share=0.00
                )
                db.session.add(merchant_revenue)
                db.session.commit()
                
                logger.info(f"Successfully inserted promo code: {code} for {merchant_revenue.merchant_name}")
                return True
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error inserting promo code {code}: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error processing coupon data: {str(e)}")
        return False

def check_database():
    """Check if database tables exist and create them if they don't."""
    try:
        with app.app_context():
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'promo_codes' not in existing_tables:
                logger.warning("Database tables not found. Creating tables...")
                db.create_all()
                logger.info("Database tables created successfully")
            else:
                logger.info("Database tables already exist")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def view_database():
    """View current database contents"""
    with app.app_context():
        print("\n=== Current Database Contents ===")
        
        # View promo codes
        print("\nPromo Codes:")
        codes = PromoCode.query.all()
        for code in codes:
            print(f"""
            Code: {code.code}
            Platform: {code.platform}
            Discount: {code.discount_value} ({code.discount_type})
            Expiration: {code.expiration_date}
            -------------------""")
            
        # View merchant revenue
        print("\nMerchant Revenue:")
        revenues = MerchantRevenue.query.all()
        for rev in revenues:
            print(f"""
            Merchant: {rev.merchant_name}
            Code: {rev.promo_code.code}
            Revenue: ${rev.revenue_generated}
            -------------------""")
            
        print(f"\nTotal Promo Codes: {len(codes)}")
        print(f"Total Merchant Entries: {len(revenues)}")    

def view_stats():
    """View database statistics"""
    with app.app_context():
        promo_count = PromoCode.query.count()
        merchant_count = MerchantRevenue.query.count()
        
        platforms = db.session.query(PromoCode.platform).distinct().all()
        platform_counts = {}
        for platform, in platforms:
            count = PromoCode.query.filter_by(platform=platform).count()
            platform_counts[platform] = count
            
        print(f"""
        Database Statistics:
        ------------------
        Total Promo Codes: {promo_count}
        Total Merchant Entries: {merchant_count}
        
        Codes by Platform:
        {platform_counts}
        """)

def main():
    with app.app_context():
        try:
            # Ensure database is ready
            check_database()
            
            # Clear any existing session
            db.session.remove()
            
            # Run RetailMeNot scraper
            retailmenot_scraper = RetailMeNotScraper()
            retailmenot_coupons = retailmenot_scraper.scrape_coupons()
            logger.info(f"Found {len(retailmenot_coupons)} RetailMeNot coupons")
            
            # Run Wired scraper
            wired_scraper = StaticPromoScraper("https://www.wired.com/coupons")
            wired_coupons = wired_scraper.fetch_all_coupons()
            logger.info(f"Found {len(wired_coupons)} Wired coupons")
            
            # Track statistics
            total_processed = 0
            total_duplicates = 0
            total_inserted = 0
            
            # Process RetailMeNot coupons
            for coupon in retailmenot_coupons:
                total_processed += 1
                if insert_promo_code(coupon, 'RetailMeNot'):
                    total_inserted += 1
                    logger.debug(f"Successfully inserted coupon {coupon.code}")
                else:
                    total_duplicates += 1
            
            # Process Wired coupons
            for coupon in wired_coupons:
                total_processed += 1
                if insert_promo_code(coupon, 'Wired'):
                    total_inserted += 1
                else:
                    total_duplicates += 1
                    
            logger.info(f"""
            Scraping Summary:
            ----------------
            Total Processed: {total_processed}
            Successfully Inserted: {total_inserted}
            Duplicates Skipped: {total_duplicates}
            """)
            
            # View results
            print("\nFinal Database State:")
            view_database()
            view_stats()
            
        except Exception as e:
            logger.error(f"Error in main scraper: {str(e)}")
            raise

if __name__ == "__main__":
    main()