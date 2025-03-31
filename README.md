# Flask Automate Docs

A Flask extension that automatically generates OpenAPI (Swagger) documentation for your Flask application's routes and SQLAlchemy models.

## Features

- Automatic route documentation extraction
- SQLAlchemy model schema generation
- Type hint support for request/response schemas
- Security scheme detection
- Beautiful Swagger UI interface
- Customizable documentation settings

## Installation

```bash
pip install flask-automate-docs
```

## Quick Start

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_automate_docs import AutomateDocs

app = Flask(__name__)
db = SQLAlchemy(app)

# Initialize the extension
docs = AutomateDocs(app, db)

# Enable documentation
app.config['AUTOMATE_DOCS_ENABLED'] = True
app.config['AUTOMATE_DOCS_SQLALCHEMY'] = True  # Enable SQLAlchemy model documentation

# Your routes and models here...

if __name__ == '__main__':
    app.run(debug=True)
```

Visit `/documentation` to see the Swagger UI interface, or `/api/docs` for the raw OpenAPI JSON.

## Configuration

The extension supports the following configuration options:

- `AUTOMATE_DOCS_ENABLED`: Enable/disable documentation (default: False)
- `AUTOMATE_DOCS_SQLALCHEMY`: Enable/disable SQLAlchemy model documentation (default: False)
- `AUTOMATE_DOCS_MODELS`: Specify models module or object (default: None)
- `AUTOMATE_DOCS_TITLE`: Documentation title (default: 'API Documentation')
- `AUTOMATE_DOCS_VERSION`: API version (default: '1.0')
- `AUTOMATE_DOCS_DESCRIPTION`: API description (default: 'Auto-generated API documentation')
- `AUTOMATE_DOCS_PATH`: Swagger UI path (default: '/documentation')
- `AUTOMATE_DOCS_JSON_PATH`: OpenAPI JSON path (default: '/api/docs')

## Type Hints

The extension supports Python type hints for better schema generation:

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    hobbies: List[str]

@app.route('/users', methods=['POST'])
def create_user(request: User) -> Dict[str, str]:
    # Your code here...
    return {"message": "User created"}
```

## Security

The extension automatically detects common security decorators:

```python
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Your authentication logic here
        return f(*args, **kwargs)
    decorated_function._login_required = True
    return decorated_function

@app.route('/protected')
@login_required
def protected_route():
    return {"message": "Protected content"}
```

## License

MIT License
