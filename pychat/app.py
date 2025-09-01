import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

from database import db, init_db
from models import User, Message, Group, Story

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pychat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
init_db(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    users = User.query.filter(User.id != current_user.id).all()
    groups = Group.query.filter(Group.members.any(id=current_user.id)).all()
    stories = Story.query.filter(Story.user_id == current_user.id).all()
    return render_template('index.html', users=users, groups=groups, stories=stories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    recipient = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read
    for message in messages:
        if message.sender_id == user_id and not message.read:
            message.read = True
    db.session.commit()
    
    return render_template('chat.html', recipient=recipient, messages=messages)

@app.route('/group/<int:group_id>')
@login_required
def group_chat(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        return redirect(url_for('index'))
    
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc()).all()
    return render_template('group_chat.html', group=group, messages=messages)

@app.route('/create_group', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    description = request.form.get('description')
    member_ids = request.form.getlist('members')
    
    group = Group(name=name, description=description, creator_id=current_user.id)
    group.members.append(current_user)
    
    for member_id in member_ids:
        member = User.query.get(member_id)
        if member:
            group.members.append(member)
    
    db.session.add(group)
    db.session.commit()
    
    return redirect(url_for('group_chat', group_id=group.id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        status = request.form.get('status')
        current_user.status = status
        
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                current_user.profile_picture = unique_filename
        
        db.session.commit()
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/upload_story', methods=['POST'])
@login_required
def upload_story():
    content = request.form.get('content')
    media_file = request.files.get('media')
    
    story = Story(user_id=current_user.id, content=content)
    
    if media_file and media_file.filename:
        filename = secure_filename(media_file.filename)
        unique_filename = f"story_{uuid.uuid4().hex}_{filename}"
        media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        story.media_url = unique_filename
    
    db.session.add(story)
    db.session.commit()
    
    return redirect(url_for('index'))

@socketio.on('connect')
@login_required
def handle_connect():
    join_room(str(current_user.id))
    emit('user_status', {'user_id': current_user.id, 'online': True}, broadcast=True)

@socketio.on('disconnect')
@login_required
def handle_disconnect():
    leave_room(str(current_user.id))
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    emit('user_status', {'user_id': current_user.id, 'online': False}, broadcast=True)

@socketio.on('private_message')
@login_required
def handle_private_message(data):
    recipient_id = data['recipient_id']
    content = data['content']
    media_type = data.get('media_type', 'text')
    media_url = data.get('media_url')
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content,
        media_type=media_type,
        media_url=media_url
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Send to sender
    emit('new_message', {
        'id': message.id,
        'sender_id': current_user.id,
        'recipient_id': recipient_id,
        'content': content,
        'media_type': media_type,
        'media_url': media_url,
        'timestamp': message.timestamp.isoformat(),
        'read': message.read,
        'sender_name': current_user.username
    }, room=str(current_user.id))
    
    # Send to recipient
    emit('new_message', {
        'id': message.id,
        'sender_id': current_user.id,
        'recipient_id': recipient_id,
        'content': content,
        'media_type': media_type,
        'media_url': media_url,
        'timestamp': message.timestamp.isoformat(),
        'read': message.read,
        'sender_name': current_user.username
    }, room=str(recipient_id))

@socketio.on('typing')
@login_required
def handle_typing(data):
    recipient_id = data['recipient_id']
    emit('user_typing', {
        'user_id': current_user.id,
        'username': current_user.username
    }, room=str(recipient_id))

@socketio.on('stop_typing')
@login_required
def handle_stop_typing(data):
    recipient_id = data['recipient_id']
    emit('user_stop_typing', {
        'user_id': current_user.id
    }, room=str(recipient_id))

if __name__ == '__main__':
    socketio.run(app, debug=True)