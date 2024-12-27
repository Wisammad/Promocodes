from flask import Blueprint, request, jsonify
from models import MerchantRevenue, db, PromoCode

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
    promo = PromoCode.query.get_or_404(data['promo_code_id'])
    
    # Calculate company share based on revenue share percentage
    revenue_generated = float(data['revenue_generated'])
    company_share = revenue_generated * float(promo.revenue_share)
    
    new_revenue = MerchantRevenue(
        merchant_name=data['merchant_name'],
        promo_code_id=data['promo_code_id'],
        revenue_generated=revenue_generated,
        company_share=company_share
    )
    
    db.session.add(new_revenue)
    db.session.commit()
    return jsonify({'message': 'Merchant revenue entry created successfully'}), 201 