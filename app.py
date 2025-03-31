from flask import Flask, request, jsonify
from typing import Dict, List
from functools import wraps
import logging
import re
from models import db, User, UserCreate

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set up configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_user_data(data: dict) -> tuple[bool, str]:
    """Validate user data."""
    if not data.get('name'):
        return False, "Name cannot be empty"
    if not validate_email(data.get('email', '')):
        return False, "Invalid email format"
    return True, ""

# Example routes with type hints
@app.route('/users', methods=['GET'])
def get_users() -> List[Dict[str, str]]:
    """Get all users."""
    users = User.query.all()
    return [{"name": user.name, "email": user.email} for user in users]

@app.route('/users', methods=['POST'])
def create_user() -> Dict[str, str]:
    """Create a new user."""
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate user data
    is_valid, error_message = validate_user_data(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    try:
        user = User(name=data['name'], email=data['email'])
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully"}
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id: int) -> Dict[str, str]:
    """Get a specific user by ID."""
    user = User.query.get_or_404(user_id)
    return {"name": user.name, "email": user.email}

# Example of a protected route
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simulate authentication
        return f(*args, **kwargs)
    decorated_function._login_required = True
    return decorated_function

@app.route('/protected')
@login_required
def protected_route():
    """This is a protected route that requires authentication."""
    return {"message": "This is protected content"}

# Debug route to check if the app is running
@app.route('/')
def index():
    """Root route to verify the app is running."""
    return {"message": "Flask Automate Docs Test App is running"}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Print all registered routes
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"{rule.endpoint}: {rule.methods} {rule}")
    app.run(debug=True) 