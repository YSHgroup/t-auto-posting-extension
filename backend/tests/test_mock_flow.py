from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_excludes_joined_and_caps_results() -> None:
    response = client.get('/api/groups/search?q=blockchain startup')
    assert response.status_code == 200
    results = response.json()
    assert len(results) <= 50
    assert all(not item['joined'] for item in results)

def test_bot_start_posts_in_mock_mode() -> None:
    client.post('/api/feed', json={'group_id': 'group_002'})
    response = client.post('/api/bot/start')
    assert response.status_code == 200
    assert response.json()['state'] == 'RUNNING'
    assert client.get('/api/history').json()[0]['status'] == 'success'

def test_bot_stop_persists_state() -> None:
    response = client.post('/api/bot/stop')
    assert response.json()['state'] == 'STOPPED'
