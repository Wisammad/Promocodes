from flask import Blueprint, request, jsonify
from models import Application, db

application_bp = Blueprint('application', __name__)

@application_bp.route('/applications', methods=['GET'])
def get_applications():
    applications = Application.query.all()
    return jsonify([{
        'id': a.id,
        'user_id': a.user_id,
        'status': a.status,
        'created_at': a.created_at,
        'updated_at': a.updated_at
    } for a in applications])

@application_bp.route('/applications', methods=['POST'])
def create_application():
    data = request.get_json()
    new_application = Application(**data)
    db.session.add(new_application)
    db.session.commit()
    return jsonify({'message': 'Application created successfully'}), 201 