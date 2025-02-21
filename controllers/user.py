from flask import Blueprint, request, jsonify, session
import bcrypt
from app import db
from models.user import User

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Cria um novo usuário
    ---
    tags:
      - Usuários
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      201:
        description: User created successfully
      400:
        description: User already exists
    """
    data = request.get_json()
    # Verifica se já existe um usuário com mesmo username
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    # Cria o usuário
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Busca um usuário pelo ID (acesso permitido somente para usuários logados)
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Retorna o objeto do usuário
      401:
        description: Login required
      404:
        description: Usuário não encontrado
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'username': user.username, 'is_admin': user.is_admin})

@user_bp.route('/users', methods=['GET'])
def list_users():
    """
    Lista todos os usuários cadastrados (acesso permitido somente para usuários logados)
    ---
    tags:
      - Usuários
    responses:
      200:
        description: Lista de usuários retornada com sucesso
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              username:
                type: string
              is_admin:
                type: boolean
      401:
        description: Login required
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    users = User.query.all()
    users_list = [{'id': user.id, 'username': user.username, 'is_admin': user.is_admin} for user in users]
    return jsonify(users_list), 200

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    """
    Edita um usuário existente.
    Se o usuário logado não for dono da conta, somente usuários administradores podem editar.
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: User updated successfully
      401:
        description: Login required
      403:
        description: Permission denied
      404:
        description: User not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    user_to_edit = User.query.get_or_404(user_id)
    
    current_user = db.session.get(User, session['user_id'])
    
    if current_user.id != user_to_edit.id and not current_user.is_admin:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    if 'username' in data:
        user_to_edit.username = data['username']
    if 'password' in data:
        hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_to_edit.password = hashed_pw

    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Deleta um usuário existente.
    Somente o próprio usuário ou administradores podem deletar um usuário.
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
    responses:
      200:
        description: User deleted successfully
      401:
        description: Login required
      403:
        description: Permission denied
      404:
        description: User not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    user_to_delete = User.query.get_or_404(user_id)
    
    current_user = db.session.get(User, session['user_id'])
    if current_user.id != user_to_delete.id and not current_user.is_admin:
        return jsonify({'message': 'Permission denied'}), 403

    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200