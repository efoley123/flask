import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# test_flask_app.py
import pytest
from unittest.mock import patch
from src.flask.app import Flask, _make_timedelta
from datetime import timedelta
from werkzeug.exceptions import BadRequestKeyError, HTTPException, InternalServerError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY='test_secret_key'
    )
    return app

def test_make_timedelta_none():
    assert _make_timedelta(None) is None

def test_make_timedelta_timedelta():
    delta = timedelta(days=1)
    assert _make_timedelta(delta) == delta

def test_make_timedelta_int():
    assert _make_timedelta(300) == timedelta(seconds=300)

def test_app_creation():
    assert Flask('test_app')

@pytest.mark.parametrize("path,status_code", [
    ("/", 404),
    ("/static/test.txt", 200),
    ("/not_found", 404)
])
def test_app_routes(app, path, status_code):
    @app.route("/static/test.txt")
    def static_file():
        return "Static file content", 200

    client = app.test_client()
    response = client.get(path)
    assert response.status_code == status_code

def test_bad_request_key_error(app):
    @app.route("/error")
    def error_route():
        raise BadRequestKeyError()

    client = app.test_client()
    response = client.get("/error")
    assert response.status_code == 400

def test_internal_server_error(app):
    @app.route("/error")
    def error_route():
        raise ValueError("An internal server error occurred")

    with patch.object(app, 'handle_exception') as handle_exception_mock:
        handle_exception_mock.side_effect = InternalServerError
        client = app.test_client()
        response = client.get("/error")
        handle_exception_mock.assert_called()
        assert response.status_code == 500

def test_custom_error_handler(app):
    @app.errorhandler(500)
    def handle_500(error):
        return 'Internal server error occurred', 500

    @app.route("/error")
    def error_route():
        raise ValueError("Triggering internal server error")

    client = app.test_client()
    response = client.get("/error")
    assert b'Internal server error occurred' in response.data
    assert response.status_code == 500

def test_get_send_file_max_age_default(app):
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 360
    assert app.get_send_file_max_age(None) == 360

def test_send_static_file_not_set(app):
    with pytest.raises(RuntimeError):
        app.send_static_file('test.txt')

def test_open_resource(app):
    with app.open_resource('__init__.py') as f:
        assert f.readable()

def test_open_instance_resource(app, tmp_path):
    d = tmp_path / "instance"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("Hello, Flask!")

    app.instance_path = str(d)
    with app.open_instance_resource('hello.txt') as f:
        assert f.read() == "Hello, Flask!"

@pytest.mark.parametrize("debug,load_dotenv,expected", [
    (True, True, True),
    (False, False, False),
    (None, True, True),
])
def test_app_run_debug_load_dotenv(monkeypatch, debug, load_dotenv, expected):
    monkeypatch.setattr('werkzeug.serving.run_simple', lambda *a, **kw: None)
    app = Flask(__name__)
    with patch.object(Flask, 'debug', debug), \
         patch.object(Flask, 'load_dotenv', load_dotenv), \
         patch('src.flask.app.cli.show_server_banner') as mock_show_banner:
        app.run()
        assert mock_show_banner.called == expected

def test_handle_http_exception(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return 'HTTPException handled', error.code

    with app.test_request_context('/'):
        resp = app.handle_http_exception(HTTPException())
        assert resp[0] == 'HTTPException handled'
        assert resp[1] == 500