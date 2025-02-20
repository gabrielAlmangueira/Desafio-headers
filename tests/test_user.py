import pytest
import bcrypt
from app import create_app
from models import db
from models.user import User

@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            # Cria dois usuários para testes:
            # user1: usuário comum
            password1 = bcrypt.hashpw("user1pass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user1 = User(username="user1", password=password1, is_admin=False)
            # user2: outro usuário comum
            password2 = bcrypt.hashpw("user2pass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user2 = User(username="user2", password=password2, is_admin=False)
            # admin: usuário administrador
            password3 = bcrypt.hashpw("adminpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = User(username="admin", password=password3, is_admin=True)
            db.session.add_all([user1, user2, admin])
            db.session.commit()
        yield client
        with flask_app.app_context():
            db.drop_all()

def login_as(client, username):
    # Entra no contexto da aplicação para executar a consulta
    with client.application.app_context():
        user = User.query.filter_by(username=username).first()
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
    return user

def test_list_users_requires_login(client):
    # Sem login, espera 401
    response = client.get("/users")
    assert response.status_code == 401
    assert b"Login required" in response.data

def test_list_users_success(client):
    # Simula login com um usuário comum e chama a rota de listar usuários
    login_as(client, "user1")
    response = client.get("/users")
    assert response.status_code == 200
    lista = response.get_json()
    # Espera 3 usuários criados pelo fixture
    assert isinstance(lista, list)
    assert len(lista) == 3

def test_edit_user_by_owner_success(client):
    # user1 edita seus próprios dados
    user = login_as(client, "user1")
    payload = {"username": "user1_updated", "password": "newuser1pass"}
    response = client.put(f"/users/{user.id}", json=payload)
    assert response.status_code == 200
    assert b"User updated successfully" in response.data

    # Verifica alteração no banco usando db.session.get()
    with client.application.app_context():
        updated_user = db.session.get(User, user.id)
        assert updated_user.username == "user1_updated"
        assert bcrypt.checkpw("newuser1pass".encode('utf-8'),
                              updated_user.password.encode('utf-8'))

def test_edit_user_by_non_owner_forbidden(client):
    # user1 tenta editar os dados de user2 e não tem permissão
    login_as(client, "user1")
    with client.application.app_context():
        user2 = User.query.filter_by(username="user2").first()
    payload = {"username": "user2_hacked"}
    response = client.put(f"/users/{user2.id}", json=payload)
    assert response.status_code == 403
    assert b"Permission denied" in response.data

def test_edit_user_by_admin_success(client):
    # admin edita os dados de user2
    login_as(client, "admin")
    with client.application.app_context():
        user2 = User.query.filter_by(username="user2").first()
    payload = {"username": "user2_updated"}
    response = client.put(f"/users/{user2.id}", json=payload)
    assert response.status_code == 200
    assert b"User updated successfully" in response.data

    with client.application.app_context():
        updated_user2 = db.session.get(User, user2.id)
        assert updated_user2.username == "user2_updated"

def test_delete_user_by_owner_success(client):
    # user2 deleta sua própria conta
    user2 = login_as(client, "user2")
    response = client.delete(f"/users/{user2.id}")
    assert response.status_code == 200
    assert b"User deleted successfully" in response.data
    with client.application.app_context():
        deleted_user = db.session.get(User, user2.id)
        assert deleted_user is None

def test_delete_user_by_non_owner_forbidden(client):
    # user1 tenta deletar a conta do admin; não permitido se não for dono nem admin
    login_as(client, "user1")
    with client.application.app_context():
        admin = User.query.filter_by(username="admin").first()
    response = client.delete(f"/users/{admin.id}")
    assert response.status_code == 403
    assert b"Permission denied" in response.data

def test_delete_user_by_admin_success(client):
    # admin deleta a conta de user1
    login_as(client, "admin")
    with client.application.app_context():
        user1 = User.query.filter_by(username="user1").first()
    response = client.delete(f"/users/{user1.id}")
    assert response.status_code == 200
    assert b"User deleted successfully" in response.data
    with client.application.app_context():
        deleted_user = db.session.get(User, user1.id)
        assert deleted_user is None