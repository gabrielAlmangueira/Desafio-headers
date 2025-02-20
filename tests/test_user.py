import pytest
from app import create_app      # Importamos create_app
from models import db           # Importamos db diretamente de models
import bcrypt
from models.user import User

@pytest.fixture
def client():
    flask_app = create_app()  # Criamos a instância da aplicação
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
        yield client
        with flask_app.app_context():
            db.drop_all()

def test_create_user_success(client):
    payload = {
        "username": "newuser",
        "password": "password123"
    }
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    assert b"User created successfully" in response.data

    # Verificando se o usuário foi salvo no banco
    with client.application.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert bcrypt.checkpw("password123".encode('utf-8'), user.password.encode('utf-8'))