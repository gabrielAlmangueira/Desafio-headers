from flask import Blueprint, request, jsonify, session
import bcrypt
from app import db
from models.post import Post
from models.user import User

post_bp = Blueprint('post_bp', __name__)

@post_bp.route('/posts', methods=['POST'])
def create_post():
    """
    Cria um post para o usuário logado
    ---
    tags:
      - Posts
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
    responses:
      201:
        description: Post created successfully
      401:
        description: Login required
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401
    
    data = request.get_json()
    new_post = Post(content=data['content'], user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully'}), 201

@post_bp.route('/posts/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    """
    Edita um post existente (apenas autor ou admin)
    ---
    tags:
      - Posts
    parameters:
      - in: path
        name: post_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          type: object
          properties:
            content:
              type: string
    responses:
      200:
        description: Post updated successfully
      401:
        description: Login required
      403:
        description: Permission denied
      404:
        description: Post not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401
    
    post = Post.query.get_or_404(post_id)
    current_user_id = session['user_id']
    current_user = User.query.get_or_404(current_user_id)

    if post.user_id != current_user_id and not current_user.is_admin:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    post.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Post updated successfully'}), 200

@post_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """
    Busca um post por id, retornando o conteúdo e os dados do autor.
    ---
    tags:
      - Posts
    parameters:
      - in: path
        name: post_id
        required: true
        type: integer
    responses:
      200:
        description: Post retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            content:
              type: string
            author:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
      401:
        description: Login required
      404:
        description: Post not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401
    
    post = Post.query.get_or_404(post_id)
    # Obter dados do autor
    author = User.query.get(post.user_id)
    response = {
        'id': post.id,
        'content': post.content,
        'author': {
            'id': author.id,
            'username': author.username
        }
    }
    return jsonify(response), 200

@post_bp.route('/posts', methods=['GET'])
def list_posts():
    """
    Lista todos os posts cadastrados, trazendo o autor (id e nome).
    ---
    tags:
      - Posts
    responses:
      200:
        description: List of posts retrieved successfully
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              content:
                type: string
              author:
                type: object
                properties:
                  id:
                    type: integer
                  username:
                    type: string
      401:
        description: Login required
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401
    
    posts = Post.query.all()
    posts_list = []
    for post in posts:
        author = User.query.get(post.user_id)
        posts_list.append({
            'id': post.id,
            'content': post.content,
            'author': {
                'id': author.id,
                'username': author.username
            }
        })
    return jsonify(posts_list), 200

@post_bp.route('/posts/user/<int:user_id>', methods=['GET'])
def list_posts_by_user(user_id):
    """
    Lista todos os posts de um usuário específico.
    ---
    tags:
      - Posts
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
    responses:
      200:
        description: List of posts by user retrieved successfully
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              content:
                type: string
      401:
        description: Login required
      404:
        description: User not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    # Certifica que o usuário existe
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).all()
    posts_list = [{'id': post.id, 'content': post.content} for post in posts]
    return jsonify(posts_list), 200

@post_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """
    Deleta um post existente.
    Somente o próprio autor ou administradores podem deletar um post.
    ---
    tags:
      - Posts
    parameters:
      - in: path
        name: post_id
        required: true
        type: integer
    responses:
      200:
        description: Post deleted successfully
      401:
        description: Login required
      403:
        description: Permission denied
      404:
        description: Post not found
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    post = Post.query.get_or_404(post_id)
    current_user_id = session['user_id']
    current_user = User.query.get_or_404(current_user_id)
    
    if post.user_id != current_user_id and not current_user.is_admin:
        return jsonify({'message': 'Permission denied'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'}), 200