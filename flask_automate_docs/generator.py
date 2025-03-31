from flask import jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from typing import Dict, List, Any, Optional, Union, get_type_hints
import traceback
import inspect
import importlib
import sys
import logging

logger = logging.getLogger(__name__)

class APIDocGenerator:
    """Core API documentation generator for Flask applications."""
    
    def __init__(self, app, db: SQLAlchemy):
        self.app = app
        self.db = db
        self.enable_docs = app.config.get('AUTOMATE_DOCS_ENABLED', False)
        self.models_source = app.config.get('AUTOMATE_DOCS_MODELS', None)
        self.title = app.config.get('AUTOMATE_DOCS_TITLE', 'API Documentation')
        self.version = app.config.get('AUTOMATE_DOCS_VERSION', '1.0')
        self.description = app.config.get('AUTOMATE_DOCS_DESCRIPTION', 'Auto-generated API documentation')
        
    def get_route_parameters(self, rule, view_func) -> List[Dict[str, Any]]:
        """Extract route parameters from URL rules."""
        parameters = []
        for param in rule.arguments:
            param_info = {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"}
            }
            parameters.append(param_info)
        return parameters

    def get_request_body(self, view_func) -> Optional[Dict[str, Any]]:
        """Extract request body schema from view function."""
        try:
            # Get function signature
            sig = inspect.signature(view_func)
            params = sig.parameters
            
            # Check if function accepts request data
            if 'request' in params:
                # Get the request type hints if available
                request_type = params['request'].annotation
                if request_type != inspect.Parameter.empty:
                    return {
                        "content": {
                            "application/json": {
                                "schema": self.get_schema_from_type(request_type)
                            }
                        }
                    }
        except Exception as e:
            logger.error(f"Error extracting request body: {str(e)}")
        return None

    def get_response_schema(self, view_func) -> Dict[str, Any]:
        """Extract response schema from view function."""
        try:
            # Get return type annotation if available
            sig = inspect.signature(view_func)
            return_type = sig.return_annotation
            
            if return_type != inspect.Parameter.empty:
                return {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": self.get_schema_from_type(return_type)
                            }
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error extracting response schema: {str(e)}")
        return {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            }
        }

    def get_schema_from_type(self, type_hint) -> Dict[str, Any]:
        """Convert Python type hints to OpenAPI schema."""
        try:
            # Handle primitive types first
            if type_hint == str:
                return {"type": "string"}
            elif type_hint == int:
                return {"type": "integer"}
            elif type_hint == float:
                return {"type": "number", "format": "float"}
            elif type_hint == bool:
                return {"type": "boolean"}
            elif type_hint == dict:
                return {"type": "object"}
            elif type_hint == list:
                return {"type": "array", "items": {"type": "object"}}
            
            # Handle generic types
            if hasattr(type_hint, "__origin__"):
                if type_hint.__origin__ is list:
                    return {
                        "type": "array",
                        "items": self.get_schema_from_type(type_hint.__args__[0])
                    }
                elif type_hint.__origin__ is dict:
                    return {
                        "type": "object",
                        "properties": {
                            k: self.get_schema_from_type(v)
                            for k, v in type_hint.__args__[1].__annotations__.items()
                        }
                    }
            
            # Handle dataclasses and other classes with annotations
            if hasattr(type_hint, "__annotations__"):
                return {
                    "type": "object",
                    "properties": {
                        k: self.get_schema_from_type(v)
                        for k, v in type_hint.__annotations__.items()
                    }
                }
            
            # Default to object type for unknown types
            return {"type": "object"}
        except Exception as e:
            logger.error(f"Error converting type to schema: {str(e)}")
            return {"type": "object"}

    def get_security_requirements(self, view_func) -> List[Dict[str, List[str]]]:
        """Extract security requirements from view function decorators."""
        security = []
        
        # Check for login_required decorator
        if hasattr(view_func, '_login_required'):
            security.append({"sessionAuth": []})
            
        # Check for admin_required decorator
        if hasattr(view_func, '_admin_required'):
            security.append({"adminAuth": []})
            
        return security

    def extract_routes(self) -> Dict[str, Dict[str, Any]]:
        """Extracts all routes with their methods, parameters, and schemas."""
        paths = {}
        
        for rule in self.app.url_map.iter_rules():
            # Skip static routes and doc routes
            if "static" in rule.endpoint or rule.endpoint in ['api_docs', 'documentation']:
                continue
                
            view_func = self.app.view_functions[rule.endpoint]
            methods = list(rule.methods - {"HEAD", "OPTIONS"})
            
            path_item = {}
            for method in methods:
                operation = {
                    "summary": view_func.__doc__ or f"{method.upper()} {rule.endpoint}",
                    "description": view_func.__doc__ or "No description provided",
                    "parameters": self.get_route_parameters(rule, view_func),
                    "responses": self.get_response_schema(view_func),
                    "security": self.get_security_requirements(view_func)
                }
                
                # Add request body if method supports it
                if method.lower() in ["post", "put", "patch"]:
                    request_body = self.get_request_body(view_func)
                    if request_body:
                        operation["requestBody"] = request_body
                
                path_item[method.lower()] = operation
            
            paths[str(rule)] = path_item
            
        return paths

    def get_models(self):
        """Get all SQLAlchemy models from the models module or current namespace."""
        models = []
        
        if self.models_source:
            # Try to import models from the specified module
            try:
                if isinstance(self.models_source, str):
                    # If it's a module name as string
                    module = importlib.import_module(self.models_source)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and hasattr(attr, '__table__'):
                            models.append(attr)
                else:
                    # If it's a module object
                    for attr_name in dir(self.models_source):
                        attr = getattr(self.models_source, attr_name)
                        if isinstance(attr, type) and hasattr(attr, '__table__'):
                            models.append(attr)
            except (ImportError, AttributeError) as e:
                logger.error(f"Error importing models: {str(e)}")
        else:
            # Fallback to current module
            current_module = sys.modules.get(self.app.name)
            if current_module:
                for attr_name in dir(current_module):
                    try:
                        attr = getattr(current_module, attr_name)
                        if isinstance(attr, type) and hasattr(attr, '__table__') and issubclass(attr, self.db.Model):
                            models.append(attr)
                    except (AttributeError, TypeError):
                        continue
                    
        return models

    def extract_models(self) -> Dict[str, Dict[str, Any]]:
        """Extracts database model schemas."""
        schemas = {}
        
        if not self.app.config.get('AUTOMATE_DOCS_SQLALCHEMY', False):
            return schemas
            
        try:
            model_classes = self.get_models()
            
            for model in model_classes:
                if isinstance(model, type) and hasattr(model, '__table__'):
                    properties = {}
                    required = []
                    
                    for col in model.__table__.columns:
                        field_type = str(col.type)
                        property_schema = {
                            "type": self.get_schema_type(field_type),
                            "description": col.doc or f"{col.name} field"
                        }
                        
                        if not col.nullable:
                            required.append(col.name)
                            
                        properties[col.name] = property_schema
                    
                    schemas[model.__name__] = {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
        except Exception as e:
            logger.error(f"Error extracting models: {str(e)}")
            logger.error(traceback.format_exc())
            
        return schemas

    def get_schema_type(self, sqlalchemy_type: str) -> str:
        """Convert SQLAlchemy type to OpenAPI schema type."""
        type_mapping = {
            "String": "string",
            "Integer": "integer",
            "Float": "number",
            "Boolean": "boolean",
            "DateTime": "string",
            "Date": "string",
            "Text": "string",
            "JSON": "object"
        }
        return type_mapping.get(sqlalchemy_type.split("(")[0], "string")

    def generate_docs(self) -> Dict[str, Any]:
        """Generate complete OpenAPI documentation."""
        try:
            return {
                "openapi": "3.0.0",
                "info": {
                    "title": self.title,
                    "version": self.version,
                    "description": self.description
                },
                "servers": [
                    {
                        "url": "/",
                        "description": "Local development server"
                    }
                ],
                "components": {
                    "schemas": self.extract_models(),
                    "securitySchemes": {
                        "sessionAuth": {
                            "type": "apiKey",
                            "in": "cookie",
                            "name": "session"
                        },
                        "adminAuth": {
                            "type": "apiKey",
                            "in": "cookie",
                            "name": "session"
                        }
                    }
                },
                "paths": self.extract_routes()
            }
        except Exception as e:
            logger.error(f"Error generating docs: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "error": "Failed to generate API documentation",
                "details": str(e)
            }

    def get_swagger_ui(self) -> str:
        """Generate Swagger UI HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css">
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script>
                window.onload = function() {
                    const ui = SwaggerUIBundle({
                        url: "{{ docs_url }}",
                        dom_id: "#swagger-ui",
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.SwaggerUIStandalonePreset
                        ],
                        layout: "BaseLayout"
                    });
                }
            </script>
        </body>
        </html>
        """.replace("{{ title }}", self.title).replace("{{ docs_url }}", "/api/docs") 