import pytest
from app import create_app 
from models import db       
import bcrypt
from models.user import User

@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            # Cria usuário para teste
            password_hash = bcrypt.hashpw(
                "test123".encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            user = User(username="testuser", password=password_hash)
            db.session.add(user)
            db.session.commit()

        yield client

        # Após os testes, dropar as tabelas
        with flask_app.app_context():
            db.drop_all()

def test_login_success(client):
    payload = {"username": "testuser", "password": "test123"}
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    assert b"Logged in successfully" in response.data
    with client.session_transaction() as sess:
        assert 'user_id' in sess

def test_login_invalid_credentials(client):
    payload = {"username": "testuser", "password": "wrongpass"}
    response = client.post("/login", json=payload)
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data

def test_logout(client):
    # Primeiro faz login
    login_payload = {"username": "testuser", "password": "test123"}
    client.post("/login", json=login_payload)
    # Agora faz logout
    response = client.post("/logout")
    assert response.status_code == 200
    assert b"Logged out" in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
        assert 'is_admin' not in sess