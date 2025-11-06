from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200


def test_create_job_queued():
    r = client.post('/api/v1/jobs', data={'sample_rate': '1'})
    assert r.status_code == 200
    data = r.json()
    assert 'job_id' in data and data['status'] == 'queued'





