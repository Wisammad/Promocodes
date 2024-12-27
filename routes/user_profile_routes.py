from flask import Blueprint, request, jsonify
from models import UserProfile, db

user_profile_bp = Blueprint('user_profile', __name__)

@user_profile_bp.route('/user-profiles', methods=['GET'])
def get_user_profiles():
    profiles = UserProfile.query.all()
    return jsonify([{
        'id': str(p.id),
        'email': p.email,
        'profile_type': p.profile_type,
        'location': p.location,
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in profiles])

@user_profile_bp.route('/user-profiles', methods=['POST'])
def create_user_profile():
    data = request.get_json()
    new_profile = UserProfile(**data)
    db.session.add(new_profile)
    db.session.commit()
    return jsonify({'message': 'User profile created successfully'}), 201 