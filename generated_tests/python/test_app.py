import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import patch
from flask import Flask, template_rendered
from src.flask.app import Flask as CustomFlask

@pytest.fixture
def app():
    app = CustomFlask(__name__)
    app.config.update({
        "TESTING": True,
        # Additional configuration for the app if necessary
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

def test_home_page(client, captured_templates):
    """Ensure the home page works."""
    response = client.get('/')
    assert response.status_code == 200
    assert len(captured_templates) == 1
    template, context = captured_templates[0]
    assert template.name == "index.html"

def test_404_page(client):
    """Ensure 404 error page works."""
    response = client.get('/path-that-does-not-exist/')
    assert response.status_code == 404

def test_static_files(client, app):
    """Ensure static files are served."""
    response = client.get('/static/example.txt')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'Example file\n'

def test_mocked_external_call(client):
    """Test a view function that makes an external call, mocked."""
    with patch('src.flask.app.external_service_call') as mock_call:
        mock_call.return_value = 'Mocked response'
        response = client.get('/external-service/')
        assert response.status_code == 200
        assert b'Mocked response' in response.data
        mock_call.assert_called_once()

def test_error_handling(client):
    """Test custom error handling."""
    response = client.get('/path-that-causes-error/')
    assert response.status_code == 500
    assert b'Internal Server Error' in response.data

def test_post_request(client):
    """Test a view function that accepts POST requests."""
    response = client.post('/submit-form/', data={'key': 'value'})
    assert response.status_code == 200
    assert b'Form submitted' in response.data

def test_template_data(client, captured_templates):
    """Test template data sent to the template."""
    response = client.get('/some-page/')
    assert response.status_code == 200
    assert len(captured_templates) == 1
    template, context = captured_templates[0]
    assert 'some_key' in context
    assert context['some_key'] == 'some_value'

# Add more tests covering different aspects of the Flask application as needed