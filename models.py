from database import db
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(50), unique=True, nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    discount_type = db.Column(db.String(20))
    discount_value = db.Column(db.Float)
    expiration_date = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer)
    revenue_share = db.Column(db.Float)
    user_profile_restriction = db.Column(db.JSON)
    location_restriction = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usage_logs = db.relationship('UsageLog', backref='promo_code', lazy=True)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user_profile', lazy=True)

class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promo_code_id = db.Column(UUID(as_uuid=True), db.ForeignKey('promo_codes.id'), nullable=False)
    user_profile_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user_profiles.id'), nullable=True)
    applied_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45))
    device_id = db.Column(db.String(255))

class MerchantRevenue(db.Model):
    __tablename__ = 'merchant_revenue'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_name = db.Column(db.String(100), nullable=False)
    promo_code_id = db.Column(UUID(as_uuid=True), db.ForeignKey('promo_codes.id'))
    revenue_generated = db.Column(db.Float, default=0.0)
    company_share = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    promo_code = db.relationship('PromoCode', backref='merchant_revenues') 