from flask import Blueprint, request, jsonify, session
from app import db
from models.post import Post
from models.user import User

post_bp = Blueprint('post_bp', __name__)

@post_bp.route('/posts', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401
    
    data = request.get_json()
    new_post = Post(content=data['content'], user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully'}), 201

@post_bp.route('/posts/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
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

# TODO Rotas para editar, buscar, listar e deletar posts