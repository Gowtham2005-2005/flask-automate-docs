from flask import Flask, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from .generator import APIDocGenerator
from typing import Optional, Union, Type
import logging

logger = logging.getLogger(__name__)

class AutomateDocs:
    """Flask extension for automatic API documentation generation."""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        self.generator = None
        
        if app is not None and db is not None:
            self.init_app(app, db)
    
    def init_app(self, app: Flask, db: SQLAlchemy):
        """Initialize the extension with Flask application."""
        self.app = app
        self.db = db
        
        # Set default configurations
        app.config.setdefault('AUTOMATE_DOCS_ENABLED', False)
        app.config.setdefault('AUTOMATE_DOCS_SQLALCHEMY', False)
        app.config.setdefault('AUTOMATE_DOCS_MODELS', None)
        app.config.setdefault('AUTOMATE_DOCS_TITLE', 'API Documentation')
        app.config.setdefault('AUTOMATE_DOCS_VERSION', '1.0')
        app.config.setdefault('AUTOMATE_DOCS_DESCRIPTION', 'Auto-generated API documentation')
        app.config.setdefault('AUTOMATE_DOCS_PATH', '/documentation')
        app.config.setdefault('AUTOMATE_DOCS_JSON_PATH', '/api/docs')
        
        # Initialize the generator
        self.generator = APIDocGenerator(app, db)
        
        # Register routes if documentation is enabled
        if app.config.get('AUTOMATE_DOCS_ENABLED'):
            self._register_routes(app)
            logger.info("AutomateDocs routes registered")
    
    def _register_routes(self, app: Flask):
        """Register documentation routes with the Flask app."""
        json_path = app.config.get('AUTOMATE_DOCS_JSON_PATH')
        ui_path = app.config.get('AUTOMATE_DOCS_PATH')
        
        @app.route(json_path)
        def api_docs():
            """Return auto-generated API documentation in OpenAPI format."""
            logger.info(f"Serving API docs at {json_path}")
            return jsonify(self.generator.generate_docs())
            
        @app.route(ui_path)
        def documentation():
            """Serve Swagger UI with auto-generated docs."""
            logger.info(f"Serving Swagger UI at {ui_path}")
            return render_template_string(self.generator.get_swagger_ui()) 