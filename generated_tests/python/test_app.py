import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import patch
from flask import Flask, template_rendered

# Setup Flask app for testing
@pytest.fixture
def app():
    app = Flask(__name__)
    return app

# Capture templates and their contexts being rendered
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

# Test normal case for rendering a template
def test_rendering_template(app, captured_templates):
    @app.route('/hello')
    def hello():
        return flask.render_template('hello.html', name='Test')

    with app.test_client() as client:
        response = client.get('/hello')
        assert response.status_code == 200
        assert len(captured_templates) == 1
        template, context = captured_templates[0]
        assert 'hello.html' in template.name
        assert context['name'] == 'Test'

# Test error case for a missing template
def test_missing_template_error(app, captured_templates):
    @app.route('/missing')
    def missing():
        return flask.render_template('missing.html')

    with app.test_client() as client:
        with pytest.raises(TemplateNotFound):
            client.get('/missing')

# Test for checking static files serving
def test_serving_static_file(app):
    with app.test_client() as client:
        response = client.get('/static/style.css')  # Assuming style.css exists under static folder
        assert response.status_code == 200

# Test for checking redirection
def test_redirection(app):
    @app.route('/redirect')
    def redirect():
        return flask.redirect('/hello')

    with app.test_client() as client:
        response = client.get('/redirect', follow_redirects=True)
        assert request.path == '/hello'

# Test for checking 404 error handling
def test_404_error(app):
    @app.route('/404')
    def error_404():
        flask.abort(404)

    with app.test_client() as client:
        response = client.get('/404')
        assert response.status_code == 404

# Test for checking session handling
def test_session_handling(app):
    @app.route('/login')
    def login():
        flask.session['user'] = 'test_user'
        return 'Logged in'

    @app.route('/logout')
    def logout():
        flask.session.pop('user', None)
        return 'Logged out'

    with app.test_client() as client:
        client.get('/login')
        with client.session_transaction() as session:
            assert session['user'] == 'test_user'
        client.get('/logout')
        with client.session_transaction() as session:
            assert 'user' not in session

# Test for checking global context processor
@pytest.fixture(autouse=True)
def global_context_processor(app):
    @app.context_processor
    def inject_global():
        return {'global_data': 'global'}

def test_global_context_processor(app, captured_templates):
    @app.route('/global')
    def global_test():
        return flask.render_template('context.html')  # Assuming context.html uses 'global_data'

    with app.test_client() as client:
        client.get('/global')
        _, context = captured_templates[0]
        assert 'global_data' in context
        assert context['global_data'] == 'global'