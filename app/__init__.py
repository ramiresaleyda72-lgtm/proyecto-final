import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # A partir de aquí, TODO debe tener 4 espacios al principio.
    # Esta línea tiene 4 espacios.
    app = Flask(__name__)

    static_path = r'C:\Users\ALEYDA\Desktop\sist_escolar\static'
   
    app.static_folder = static_path
    
    template_path = r'C:\Users\ALEYDA\Desktop\sist_escolar\templates'
    
    
    app.template_folder = template_path

    app.config.from_object('app.config.Config')

    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Usuario 
        return Usuario.query.get(int(user_id))

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.estudiante import estudiante_bp
    from .routes.docente import docente_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(estudiante_bp, url_prefix='/estudiante')
    app.register_blueprint(docente_bp, url_prefix='/docente')

    with app.app_context():
        from . import models
        db.create_all()
        
        from .models import Usuario
        if not Usuario.query.filter_by(nombre_usuario='admin').first():
            admin_user = Usuario(nombre_usuario='admin', rol='ADMIN')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario admin creado con contraseña 'admin123'")

    return app