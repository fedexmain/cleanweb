import os
import random
import click
from flask.cli import with_appcontext
from app import create_app, db
from app.models import User, Role, Message, Notification, PackageType, Package
from flask_migrate import Migrate
import unittest
from tests import test_user_model

app = create_app(os.getenv('CONFIG') or 'default')
migrate = Migrate(app, db)

# Flask shell context
@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Message=Message,
                Notification=Notification, PackageType=PackageType, Package=Package)

# Database migration command (Flask-Migrate already works with Flask CLI)
# So you can now use: flask db init / migrate / upgrade etc.

@app.cli.command("test")
@with_appcontext
def run_tests():
    """Run the unit tests."""
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command("runserver")
@click.option('--host', default='0.0.0.0', help='Host to run on.')
@click.option('--port', default=5000, help='Port to run on.')
@click.option('--debug', is_flag=True, default=True, help='Enable debug mode.')
@with_appcontext
def runserver(host='0.0.0.0', port=5000, debug=True):
    """Run the server with custom host and port."""
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(e)

@app.cli.command("runserver_random")
@with_appcontext
def runserver_on_random_port():
    """Run the server on a random port."""
    port = int(''.join(random.choices('56789', k=4)))
    print(f"\nRunning on random port: {port}\n")
    try:
        app.run(port=port, debug=True)
    except Exception as e:
        print(e)

# Optional: custom test command if test_user_model is callable
@app.cli.command("custom_test")
@with_appcontext
def run_custom_test():
    """Run custom user model test."""
    test_user_model()
