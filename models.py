from database import db
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSON

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(50), unique=True, nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=False)
    user_profile_restriction = db.Column(JSON, nullable=True)
    location_restriction = db.Column(JSON, nullable=True)
    revenue_share = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usage_logs = db.relationship('UsageLog', backref='promo_code', lazy=True)
    merchant_revenues = db.relationship('MerchantRevenue', backref='promo_code', lazy=True)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=True)
    profile_type = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user_profile', lazy=True)

class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promo_code_id = db.Column(UUID(as_uuid=True), db.ForeignKey('promo_codes.id'), nullable=False)
    user_profile_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user_profiles.id'), nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    device_id = db.Column(db.String(255), nullable=True)

class MerchantRevenue(db.Model):
    __tablename__ = 'merchant_revenue'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_name = db.Column(db.String(255), nullable=False)
    promo_code_id = db.Column(UUID(as_uuid=True), db.ForeignKey('promo_codes.id'), nullable=False)
    revenue_generated = db.Column(db.Numeric(10, 2), nullable=False)
    company_share = db.Column(db.Numeric(10, 2), nullable=False)
    tracked_at = db.Column(db.DateTime, default=datetime.utcnow) 