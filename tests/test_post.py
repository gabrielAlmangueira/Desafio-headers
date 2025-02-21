import pytest
import bcrypt
from app import create_app
from models import db
from models.user import User
from models.post import Post

@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            # Cria usuários para testes
            password1 = bcrypt.hashpw("user1pass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user1 = User(username="user1", password=password1, is_admin=False)
            password2 = bcrypt.hashpw("adminpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = User(username="admin", password=password2, is_admin=True)
            db.session.add_all([user1, admin])
            db.session.commit()
        yield client
        with flask_app.app_context():
            db.drop_all()

def login_as(client, username):
    # Executa dentro do contexto da aplicação para obter o usuário
    with client.application.app_context():
        user = User.query.filter_by(username=username).first()
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
    return user

def create_post_helper(client, content):
    # Cria um post e retorna os dados do post criado
    response = client.post("/posts", json={"content": content})
    assert response.status_code == 201
    return response.get_json()

def test_create_post_requires_login(client):
    response = client.post("/posts", json={"content": "Teste sem login"})
    assert response.status_code == 401
    assert b"Login required" in response.data

def test_create_post_success(client):
    user = login_as(client, "user1")
    response = client.post("/posts", json={"content": "Meu primeiro post"})
    assert response.status_code == 201
    assert b"Post created successfully" in response.data

def test_get_post_success(client):
    login_as(client, "user1")
    # Cria um post
    response = client.post("/posts", json={"content": "Post de teste"})
    assert response.status_code == 201
    # Recupera o id do post criado
    with client.application.app_context():
        post = Post.query.first()
    get_response = client.get(f"/posts/{post.id}")
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data['id'] == post.id
    assert data['content'] == post.content
    assert 'author' in data
    assert data['author']['id'] == post.user_id

def test_list_posts_requires_login(client):
    response = client.get("/posts")
    assert response.status_code == 401
    assert b"Login required" in response.data

def test_list_posts_success(client):
    login_as(client, "user1")
    # Cria 2 posts
    client.post("/posts", json={"content": "Post 1"})
    client.post("/posts", json={"content": "Post 2"})
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2  # podem existir posts de outros testes também

def test_list_posts_by_user_success(client):
    # Cria outro usuário e posts
    login_as(client, "user1")
    client.post("/posts", json={"content": "User1 post"})
    with client.application.app_context():
        user1 = User.query.filter_by(username="user1").first()
    response = client.get(f"/posts/user/{user1.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Cada post deve pertencer ao usuário indicado
    for post in data:
        assert 'content' in post

def test_edit_post_by_author_success(client):
    login_as(client, "user1")
    # Cria um post
    client.post("/posts", json={"content": "Post original"})
    with client.application.app_context():
        post = Post.query.first()
    # Autor edita seu post
    payload = {"content": "Post editado"}
    response = client.put(f"/posts/{post.id}", json=payload)
    assert response.status_code == 200
    assert b"Post updated successfully" in response.data
    with client.application.app_context():
        updated_post = db.session.get(Post, post.id)
        assert updated_post.content == "Post editado"

def test_edit_post_by_admin_success(client):
    # user1 cria um post e admin tenta editar, mas admin tem permissão
    login_as(client, "user1")
    client.post("/posts", json={"content": "Post de user1"})
    with client.application.app_context():
        post = Post.query.first()
    # user1 tenta editar com outro usuário não admin
    # Para simular, registra admin na sessão e tenta editar post de user1
    login_as(client, "admin")
    payload = {"content": "Tentativa de edição"}
    response = client.put(f"/posts/{post.id}", json=payload)
    # Admin tem permissão para editar posts de outros usuários
    assert response.status_code == 200
    assert b"Post updated successfully" in response.data

def test_edit_post_by_non_author_forbidden(client):
    # Cria um post com user1
    login_as(client, "user1")
    response = client.post("/posts", json={"content": "Post de user1"})
    assert response.status_code == 201
    
    with client.application.app_context():
        post = Post.query.first()
        assert post is not None

    # Certifica que existe um usuário não administrador, diferente de user1
    with client.application.app_context():
        from models.user import User
        user2 = User.query.filter_by(username="user2").first()
        if not user2:
            import bcrypt
            password = bcrypt.hashpw("user2pass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user2 = User(username="user2", password=password, is_admin=False)
            db.session.add(user2)
            db.session.commit()

    # Agora, login com user2 (não autor do post) e tenta editar o post de user1
    login_as(client, "user2")
    payload = {"content": "Tentativa de edição não autorizada"}
    response = client.put(f"/posts/{post.id}", json=payload)
    
    # Verifica que a edição é negada com status 403 e mensagem de permissão negada
    assert response.status_code == 403
    assert b"Permission denied" in response.data

def test_delete_post_by_author_success(client):
    login_as(client, "user1")
    client.post("/posts", json={"content": "Post para deleção"})
    with client.application.app_context():
        post = Post.query.first()
    response = client.delete(f"/posts/{post.id}")
    assert response.status_code == 200
    assert b"Post deleted successfully" in response.data
    with client.application.app_context():
        deleted_post = db.session.get(Post, post.id)
        assert deleted_post is None

def test_delete_post_by_non_author_forbidden(client):
    login_as(client, "user1")
    client.post("/posts", json={"content": "Post que não poderá ser deletado"})
    with client.application.app_context():
        post = Post.query.first()
    # Tentar deletar com outro usuário não admin
    login_as(client, "admin")
    # Admin tem permissão; para testar proibição, precisamos de outro usuário não-author e não-admin.
    # Assim vamos criar um novo usuário
    with client.application.app_context():
        from models.user import User
        password = bcrypt.hashpw("user2pass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user2 = User(username="user2", password=password, is_admin=False)
        db.session.add(user2)
        db.session.commit()
    login_as(client, "user2")
    response = client.delete(f"/posts/{post.id}")
    # Como user2 não é o autor de post nem admin, a deleção deve ser negada.
    assert response.status_code == 403
    assert b"Permission denied" in response.data

def test_delete_post_by_admin_success(client):
    login_as(client, "user1")
    client.post("/posts", json={"content": "Post deletável por admin"})
    with client.application.app_context():
        post = Post.query.first()
    # Admin deleta o post
    login_as(client, "admin")
    response = client.delete(f"/posts/{post.id}")
    assert response.status_code == 200
    assert b"Post deleted successfully" in response.data
    with client.application.app_context():
        deleted_post = db.session.get(Post, post.id)
        assert deleted_post is None