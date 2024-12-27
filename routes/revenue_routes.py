from flask import Blueprint, request, jsonify
from models import MerchantRevenue, db

revenue_bp = Blueprint('revenue', __name__)

@revenue_bp.route('/merchant-revenue', methods=['GET'])
def get_merchant_revenue():
    revenues = MerchantRevenue.query.all()
    return jsonify([{
        'id': str(r.id),
        'merchant_name': r.merchant_name,
        'promo_code_id': str(r.promo_code_id),
        'revenue_generated': float(r.revenue_generated),
        'company_share': float(r.company_share),
        'tracked_at': r.tracked_at.isoformat()
    } for r in revenues])

@revenue_bp.route('/merchant-revenue', methods=['POST'])
def create_merchant_revenue():
    data = request.get_json()
    new_revenue = MerchantRevenue(**data)
    db.session.add(new_revenue)
    db.session.commit()
    return jsonify({'message': 'Merchant revenue entry created successfully'}), 201 