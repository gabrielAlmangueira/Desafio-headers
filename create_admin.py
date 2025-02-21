import bcrypt
from app import create_app
from models import db
from models.user import User

app = create_app()

with app.app_context():
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        password = "admin"
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(username="admin", password=hashed_pw, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe!")