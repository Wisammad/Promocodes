from app import app
from database import db
from models import PromoCode, MerchantRevenue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database"""
    with app.app_context():
        try:
            # Drop all tables
            logger.info("Dropping all tables...")
            db.drop_all()
            
            # Create all tables
            logger.info("Creating all tables...")
            db.create_all()
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {tables}")
            
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False

if __name__ == "__main__":
    init_database() 