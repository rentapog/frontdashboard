from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///seobrain.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    # Flask-Mail config (placeholders)
    app.config['MAIL_SERVER'] = 'smtp.resend.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'resend'
    app.config['MAIL_PASSWORD'] = 're_KTKcZQmW_PEXewn5aHGm53qy9VRCJfMvJ'
    app.config['MAIL_DEFAULT_SENDER'] = 'seobrainai@yourdomain.com'
    mail.init_app(app)

    import models
    with app.app_context():
        db.create_all()

    import routes
    app.register_blueprint(routes.bp)

    from flask import render_template
    @app.route('/')
    def index():
        return render_template('packages.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
