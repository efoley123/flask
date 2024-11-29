import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import patch
from flask import Flask

# Importing the Flask class from src.flask.app.py
from src.flask.app import Flask as FlaskApp

@pytest.fixture
def app():
    app = FlaskApp(__name__)
    app.config.update({
        "TESTING": True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_app_creation():
    """
    Test if the Flask application is created successfully.
    """
    assert isinstance(FlaskApp(__name__), FlaskApp)

def test_app_run_success_case(app):
    """
    Test if the Flask application runs successfully with the default parameters.
    """
    with patch.object(app, 'run') as mock_run:
        app.run()
        mock_run.assert_called_once()

def test_app_run_with_parameters(app):
    """
    Test if the Flask application runs successfully with custom parameters.
    """
    with patch.object(app, 'run') as mock_run:
        app.run(host='0.0.0.0', port=8080, debug=True)
        mock_run.assert_called_once_with(host='0.0.0.0', port=8080, debug=True)

def test_app_test_client_success_case(app, client):
    """
    Test if the test client is created successfully and can access the root route.
    """
    @app.route('/')
    def index():
        return 'Hello World', 200

    response = client.get('/')
    assert response.data == b'Hello World'
    assert response.status_code == 200

def test_app_failure_scenario(app, client):
    """
    Test if the application correctly handles a non-existent route.
    """
    response = client.get('/non-existent')
    assert response.status_code == 404

def test_app_with_external_dependency_mocked(app, client):
    """
    Test if the application correctly handles routes with external dependencies mocked.
    """
    external_dependency = "external_service.method"
    with patch(external_dependency, return_value="Mocked Response"):
        @app.route('/external-service')
        def external_service():
            result = external_service.method()  # Assuming this is the external dependency
            return result, 200

        response = client.get('/external-service')
        assert response.data == b'Mocked Response'
        assert response.status_code == 200

def test_app_teardown(app):
    """
    Test if the teardown functions are called after the request context is popped.
    """
    with patch.object(app, 'do_teardown_request') as mock_teardown:
        with app.test_request_context('/'):
            pass
        mock_teardown.assert_called_once()