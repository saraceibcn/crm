from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    @app.route("/health")
    def health():
        return {"status": "healthy"}
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    mail.init_app(app)

    from backend.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from backend.blueprints.usuarios import usuarios_bp
    from backend.blueprints.alumnos import alumnos_bp
    from backend.blueprints.postulados import postulados_bp
    from backend.blueprints.matricula import matricula_bp
    from backend.blueprints.publicidad import publicidad_bp


    from backend.blueprints.filtros import filtros_bp
    from backend.blueprints.comentarios_perfil import comentarios_bp
    from backend.blueprints.masters import masters_bp
    from backend.blueprints.exportar import export_bp
    from backend.blueprints.usuario_detalle import usuario_detalle_bp
    from backend.blueprints.historial import historial_bp
    from backend.blueprints.users_sistema import users_sistema_bp
    from backend.blueprints.presets import presets_bp
    from backend.blueprints.email import email_bp
    from backend.blueprints.firmas import firma_bp
    # Registrar
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(alumnos_bp)
    app.register_blueprint(postulados_bp)
    app.register_blueprint(matricula_bp)
    app.register_blueprint(filtros_bp)
    app.register_blueprint(masters_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(usuario_detalle_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(users_sistema_bp)
    app.register_blueprint(presets_bp)
    app.register_blueprint(publicidad_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(comentarios_bp)
    app.register_blueprint(firma_bp)
    return app
