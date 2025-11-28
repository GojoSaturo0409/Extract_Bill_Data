import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_extract_endpoint_missing_body(client):
    response = client.post('/extract-bill-data')
    assert response.status_code == 400

def test_extract_endpoint_missing_document(client):
    response = client.post('/extract-bill-data', 
        json={},
        content_type='application/json')
    assert response.status_code == 400

def test_extract_endpoint_invalid_content_type(client):
    response = client.post('/extract-bill-data',
        data='not json')
    assert response.status_code == 400

def test_404_endpoint(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404
