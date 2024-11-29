import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import patch
from flask import Flask, template_rendered
from src.flask.app import Flask as FlaskApp

@pytest.fixture
def app():
    app = FlaskApp(__name__)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_flask_app_creation():
    """
    Test Flask application creation.
    """
    app = FlaskApp(__name__)
    assert app is not None

def test_flask_app_run_with_mocked_server(app):
    """
    Test Flask app.run with mocked server to ensure it doesn't actually run.
    """
    with patch("werkzeug.serving.run_simple") as mock_run:
        app.run()
    mock_run.assert_called()

def test_app_test_client_can_access_test_endpoint(app, client):
    """
    Test accessing a test endpoint with the test client.
    """
    @app.route('/test')
    def test_endpoint():
        return "Test response", 200
    
    response = client.get('/test')
    assert response.status_code == 200
    assert response.data == b"Test response"

def test_app_handle_exception(app, client):
    """
    Test app's ability to handle exceptions.
    """
    @app.route('/error')
    def error_endpoint():
        raise ValueError("Intentional error")
    
    with pytest.raises(ValueError):
        client.get('/error')

def test_template_rendering(app, client):
    """
    Test rendering templates with Flask.
    """
    @app.route('/hello')
    def hello():
        return template_rendered("hello.html", name="Test")

    with app.app_context():
        captured_templates = []
        def record(sender, template, context, **extra):
            captured_templates.append((template, context))
        template_rendered.connect(record, app)
        
        client.get('/hello')
        
        assert len(captured_templates) == 1
        template, context = captured_templates[0]
        assert template.name == "hello.html"
        assert context['name'] == "Test"

def test_static_file_serving(app, client):
    """
    Test serving static files.
    """
    response = client.get('/static/example.txt')
    assert response.status_code == 200
    assert b"This is an example static file." in response.data

def test_custom_template_loader(app):
    """
    Test custom template loader functionality.
    """
    class CustomLoader:
        def get_source(self, environment, template):
            return "Custom loader response", template, lambda: True
    
    app.jinja_loader = CustomLoader()
    
    @app.route('/custom_loader')
    def custom_loader():
        return template_rendered("any_template.html")

    response = client.get('/custom_loader')
    assert b"Custom loader response" in response.data