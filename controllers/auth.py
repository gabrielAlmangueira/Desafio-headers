from flask import Blueprint, request, jsonify, session
import bcrypt
from models.user import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuário
    ---
    tags:
      - Autenticação
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
      200:
        description: Logged in successfully
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password').encode('utf-8')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({'message': 'Logged in successfully'}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout de usuário
    ---
    tags:
      - Autenticação
    responses:
      200:
        description: Logged out
    """
    session.clear()
    return jsonify({'message': 'Logged out'}), 200