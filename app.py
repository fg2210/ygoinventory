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
# app.secret_key = os.urandom(24)  # Secret key for session management

# Database connection
# def get_database_connection():
#     try:
#         return mysql.connector.connect(
#             host="localhost",
#             user="root",  # Replace with your MySQL user
#             password="",  # Replace with your MySQL password
#             database="ygoinventory"
#         )
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return None


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ygoinventory.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLE
class InventoryCard(db.Model):
    __tablename__ = "CardData"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    card_type: Mapped[str] = mapped_column(String(100), nullable=False)
    card_secondary_type: Mapped[str] = mapped_column(String(100), nullable=False)
    card_description: Mapped[str] = mapped_column(Text, nullable=False)
    card_race: Mapped[str] = mapped_column(String(100), nullable=False)
    card_archetype: Mapped[str] = mapped_column(String(255), nullable=False)
    card_atk: Mapped[int] = mapped_column(Integer(11), nullable=False)
    card_def: Mapped[int] = mapped_column(Integer(11), nullable=False)
    card_level: Mapped[int] = mapped_column(Integer(11), nullable=False)
    card_attribute: Mapped[str] = mapped_column(String(50), nullable=False)
    card_link_value: Mapped[int] = mapped_column(Integer(11), nullable=False)
    card_pend_desc: Mapped[str] = mapped_column(Text, nullable=False)
    card_monster_desc: Mapped[str] = mapped_column(Text, nullable=False)
    card_scale: Mapped[int] = mapped_column(Integer(11), nullable=False)
    card_code: Mapped[str] = mapped_column(String(50), nullable=False)
    set_code: Mapped[str] = mapped_column(String(50), nullable=False)
    card_rarity: Mapped[str] = mapped_column(String(100), nullable=False)
    card_rarity_id: Mapped[str] = mapped_column(String(255), nullable=False)

class Users(UserMixin, db.Model):
    __tablename__ = "UserData"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

with app.app_context():
    db.create_all()

# Sanitize filename function: only remove "?"
def sanitize_filename(name):
    return name.replace('?', '').replace('/', '').replace(':', '').replace('"', '')

# Sanitize filename function: only remove "?"
def sanitize_filename_set(name):
    return name.replace('?', '').replace('/', '_').replace(':', '_').replace('"', '_').replace("'", '_')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))  # Redirect to the home page if not logged in
        return f(*args, **kwargs)
    return decorated_function

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')  # Get email from the form
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate the email format using regex
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        # Check if the username already exists
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM ygoinventoryuserdata WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already taken. Please choose a different one.', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('register'))

        # Check if the email already exists
        query = "SELECT * FROM ygoinventoryuserdata WHERE email = %s"
        cursor.execute(query, (email,))
        existing_email = cursor.fetchone()

        if existing_email:
            flash('Email already registered. Please use a different email.', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Insert the new user into the database
        insert_query = "INSERT INTO ygoinventoryuserdata (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (username, email, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.before_request
def check_login_status():
    # Check if user is logged in and tries to access the login page
    if 'username' in session and request.endpoint == 'index':
        session.pop('username', None)  # Log the user out if they try to go to the login page
        flash('You have been logged out.', 'info')
        return redirect(url_for('sets'))  # Redirect to the sets page or another page


# Route for login
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate login credentials (replace with your database logic)
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM ygoinventoryuserdata WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and check_password_hash(user['password'], password):  # Compare hashed passwords
            session['username'] = user['username']  # Set the username in session
            flash('Login successful!', 'success')  # Success message
            return redirect(url_for('sets'))  # Redirect to sets page after login
        else:
            flash('Invalid username or password.', 'danger')  # Failure message

    return render_template('index.html')




# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # Redirect back to the login page

# Fetch card sets from the database
def get_card_sets():
    connection = get_database_connection()
    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True, buffered=True)
    query = """
        SELECT * FROM ygoinventorysetlist
        WHERE EXISTS (
            SELECT 1 FROM ygoinventorycardlist WHERE ygoinventorycardlist.set_code = ygoinventorysetlist.set_code
        )
    """
    cursor.execute(query)
    card_sets = cursor.fetchall()  # Fetch all results
    cursor.close()
    connection.close()
    return card_sets

# Fetch cards by set code
def get_cards_by_set(set_code):
    connection = get_database_connection()
    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True, buffered=True)
    query = "SELECT * FROM ygoinventorycardlist WHERE set_code = %s"
    cursor.execute(query, (set_code,))
    matching_cards = cursor.fetchall()  # Fetch all results
    cursor.close()
    connection.close()

    for card in matching_cards:
        sanitized_name = sanitize_filename(card['card_name'])
        image_path = os.path.join(app.static_folder, 'card_images', f"{sanitized_name}.jpg")
        if os.path.exists(image_path):
            card['card_image'] = url_for('static', filename=f'card_images/{sanitized_name}.jpg')
        else:
            card['card_image'] = url_for('static', filename='card_images/card.jpg')  # Default image if not found

    return matching_cards

# Fetch user card data from the database based on the logged-in username
def get_user_card_info(username):
    connection = get_database_connection()
    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT * FROM ygoinventoryusercarddata
        WHERE username = %s
    """
    cursor.execute(query, (username,))
    user_card_info = cursor.fetchall()
    cursor.close()
    connection.close()
    return user_card_info


@app.route('/sets')
@login_required
def sets():
    card_sets = get_card_sets()
    valid_sets = [s for s in card_sets if s.get('tcg_date')]
    unknown_sets = [s for s in card_sets if not s.get('tcg_date')]
    valid_sets = sorted(valid_sets, key=lambda x: x['tcg_date'], reverse=True)
    unique_years = sorted({s['tcg_date'].year for s in valid_sets}, reverse=True)

    for card_set in valid_sets + unknown_sets:
        sanitized_name_sets = sanitize_filename_set(card_set['set_name'])
        image_path = os.path.join(app.static_folder, 'set_images', f"{sanitized_name_sets}.jpg")
        if os.path.exists(image_path):
            card_set['set_image'] = url_for('static', filename=f'set_images/{sanitized_name_sets}.jpg')
        else:
            card_set['set_image'] = url_for('static', filename='set_images/yugioh_logo.png')  # Default logo image

    current_date = datetime.now().date()
    return render_template('sets.html', card_sets=valid_sets, unknown_sets=unknown_sets, unique_years=unique_years,
                           current_date=current_date)

@app.route('/set_list/<set_code>')
@login_required
def set_list(set_code):
    card_sets = get_card_sets()
    selected_set = next((s for s in card_sets if s['set_code'] == set_code), None)

    if not selected_set:
        return render_template('set_not_found.html', set_code=set_code)

    matching_cards = get_cards_by_set(set_code)
    username = session['username']  # Get the logged-in username
    user_card_info = get_user_card_info(username)

    # Create a set of matching card_rarity_ids for fast lookup
    matching_rarity_ids = {user_card['card_rarity_id'] for user_card in user_card_info}

    for card in matching_cards:
        card['sanitized_name'] = sanitize_filename_set(card['card_name'])
        # Add a flag to indicate whether the card should be highlighted
        card['highlight'] = card['card_rarity_id'] in matching_rarity_ids

    return render_template('set_list.html', selected_set=selected_set, matching_cards=matching_cards,
                           user_card_info=user_card_info)


@app.route('/card_info/<card_name>')
@login_required
def card_info(card_name):
    card_details = get_card_details_by_name(card_name)
    unique_card_codes = get_unique_card_codes(card_name)

    if not card_details:
        return render_template('card_not_found.html', card_name=card_name)

    card_details['sanitized_name'] = sanitize_filename(card_name)

    return render_template('card_info.html', card_details=card_details, unique_card_codes=unique_card_codes)

# Fetch card details by name
@login_required
def get_card_details_by_name(card_name):
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM ygoinventorycardlist WHERE card_name = %s"
    cursor.execute(query, (card_name,))
    card_details = cursor.fetchone()

    if card_details:
        sanitized_name = sanitize_filename(card_name)
        image_path = os.path.join(app.static_folder, 'card_images', f"{sanitized_name}.jpg")
        if os.path.exists(image_path):
            card_details['card_image'] = url_for('static', filename=f'card_images/{sanitized_name}.jpg')
        else:
            card_details['card_image'] = url_for('static', filename='card_images/card.jpg')

    connection.close()
    return card_details

# Fetch unique card codes for a specific card name
@login_required
def get_unique_card_codes(card_name):
    connection = get_database_connection()
    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True, buffered=True)
    query = "SELECT DISTINCT card_code, set_code FROM ygoinventorycardlist WHERE card_name = %s"
    cursor.execute(query, (card_name,))
    unique_card_codes = cursor.fetchall()
    cursor.close()
    connection.close()
    return unique_card_codes


if __name__ == '__main__':
    app.run(debug=True)