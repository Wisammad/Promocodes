import sys
import os

# Add the project root to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app
from models import db, PromoCode
from flask import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_add_promo_code(client):
    # Test with valid data
    response = client.post('/api/promo-codes', data=json.dumps({
        'code': 'TESTCODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 100
    }), content_type='application/json')
    assert response.status_code == 201
    assert b'Promo code added successfully' in response.data

    # Test with invalid data (missing required fields)
    response = client.post('/api/promo-codes', data=json.dumps({
        'platform': 'Amazon'
    }), content_type='application/json')
    assert response.status_code == 400

    # Test with duplicate promo code
    response = client.post('/api/promo-codes', data=json.dumps({
        'code': 'TESTCODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 100
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Promo code already exists' in response.data

    # Test with invalid data type
    response = client.post('/api/promo-codes', data=json.dumps({
        'code': 'INVALIDTYPE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 'ten',
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 100
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Invalid discount value' in response.data

def test_apply_promo_code(client):
    # First, add a promo code
    client.post('/api/promo-codes', data=json.dumps({
        'code': 'TESTCODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 1
    }), content_type='application/json')

    # Test applying the promo code successfully
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'TESTCODE',
        'user_profile_id': None,
        'location': 'US',
        'profile_type': None
    }), content_type='application/json')
    assert response.status_code == 200
    assert b'Promo code applied successfully' in response.data

    # Test applying the promo code again (usage limit reached)
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'TESTCODE',
        'user_profile_id': None,
        'location': 'US',
        'profile_type': None
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Usage limit exceeded' in response.data

    # Test applying an expired promo code
    client.post('/api/promo-codes', data=json.dumps({
        'code': 'EXPIREDCODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2000-12-31T23:59:59',
        'usage_limit': 100
    }), content_type='application/json')
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'EXPIREDCODE',
        'user_profile_id': None,
        'location': 'US',
        'profile_type': None
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Promo code has expired' in response.data

    # Test applying an invalid promo code
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'INVALIDCODE',
        'user_profile_id': None,
        'location': 'US',
        'profile_type': None
    }), content_type='application/json')
    assert response.status_code == 404
    assert b'Invalid promo code' in response.data

    # Test location restriction
    client.post('/api/promo-codes', data=json.dumps({
        'code': 'LOCATEDCODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 100,
        'location_restriction': ['US']
    }), content_type='application/json')
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'LOCATEDCODE',
        'user_profile_id': None,
        'location': 'CA',
        'profile_type': None
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Location not eligible' in response.data

    # Test profile type restriction
    client.post('/api/promo-codes', data=json.dumps({
        'code': 'PROFILECODE',
        'platform': 'Amazon',
        'discount_type': 'percentage',
        'discount_value': 10.00,
        'expiration_date': '2025-12-31T23:59:59',
        'usage_limit': 100,
        'user_profile_restriction': ['premium']
    }), content_type='application/json')
    response = client.post('/api/apply-code', data=json.dumps({
        'code': 'PROFILECODE',
        'user_profile_id': None,
        'location': 'US',
        'profile_type': 'basic'
    }), content_type='application/json')
    assert response.status_code == 400
    assert b'Profile type not eligible' in response.data 