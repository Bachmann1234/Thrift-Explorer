import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_mapping(
            SECRET_KEY=os.environ["SECRET_KEY"]
        )
    @app.route('/health')
    def hello():
        return 'Howdy!'
    return app