from flask import Flask, render_template, url_for, request, redirect, flash, session
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_gravatar import Gravatar
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

# Database Configuration
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ygoinventory.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Models
class InventoryCard(db.Model):
    # Primary Key: card_rarity_id
    # Links to UserCardData by card_rarity_id
    # Links to SetData by set_code
    __tablename__ = "CardData"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    card_type: Mapped[str] = mapped_column(String(100), nullable=False)
    card_secondary_type: Mapped[str] = mapped_column(String(100), nullable=False)
    card_description: Mapped[str] = mapped_column(Text, nullable=False)
    card_race: Mapped[str] = mapped_column(String(100), nullable=False)
    card_archetype: Mapped[str] = mapped_column(String(255), nullable=False)
    card_atk: Mapped[int] = mapped_column(Integer, nullable=False)
    card_def: Mapped[int] = mapped_column(Integer, nullable=False)
    card_level: Mapped[int] = mapped_column(Integer, nullable=False)
    card_attribute: Mapped[str] = mapped_column(String(50), nullable=False)
    card_link_value: Mapped[int] = mapped_column(Integer, nullable=True)
    card_pend_desc: Mapped[str] = mapped_column(Text, nullable=True)
    card_monster_desc: Mapped[str] = mapped_column(Text, nullable=True)
    card_scale: Mapped[int] = mapped_column(Integer, nullable=True)
    card_code: Mapped[str] = mapped_column(String(50), nullable=False)
    set_code: Mapped[str] = mapped_column(String(50), nullable=False)
    card_rarity: Mapped[str] = mapped_column(String(100), nullable=False)
    card_rarity_id: Mapped[str] = mapped_column(String(255), nullable=False)

class Users(UserMixin, db.Model):
    __tablename__ = "UserData"
    # Primary Key: user_id
    # Links to UserCardData user_id
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

class Sets(db.Model):
    __tablename__ = "SetData"
    # Primary Key: set_code
    # Links to CardData by set_code
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    set_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    set_name: Mapped[str] = mapped_column(String(255), nullable=False)
    set_type: Mapped[str] = mapped_column(String(255), nullable=False)
    set_date: Mapped[datetime] = mapped_column(datetime)

class UserCardData(db.Model):
    __tablename__ = "UserCardData"
    # Links to UserCardData by card_rarity_id
    # Links to CardData by card_rarity_id
    # Links to UserData by user_id
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    set_code: Mapped[str] = mapped_column(String(255), nullable=False)
    card_edition: Mapped[str] = mapped_column(String(255), nullable=False)
    card_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    card_rarity_id: Mapped[str] = mapped_column(String(255), nullable=False)


# Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# Utility Functions
def sanitize_filename(name):
    """Sanitize file names, only removing '?' and other unsafe characters."""
    return name.replace('?', '')

def login_required(f):
    """Decorator to protect routes from unauthorized access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return "Welcome to YGO Inventory!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Email validation
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            flash('Invalid email address.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        # Create user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = Users(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

# Initialize Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
