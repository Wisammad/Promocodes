from flask import Blueprint, request, jsonify
from models import Revenue, db

revenue_bp = Blueprint('revenue', __name__)

@revenue_bp.route('/revenue', methods=['GET'])
def get_revenue():
    revenues = Revenue.query.all()
    return jsonify([{
        'id': r.id,
        'amount': r.amount,
        'source': r.source,
        'date': r.date
    } for r in revenues])

@revenue_bp.route('/revenue', methods=['POST'])
def create_revenue():
    data = request.get_json()
    new_revenue = Revenue(**data)
    db.session.add(new_revenue)
    db.session.commit()
    return jsonify({'message': 'Revenue entry created successfully'}), 201 