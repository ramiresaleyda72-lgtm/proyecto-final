from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum
from app import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('ADMIN', 'DOCENTE', 'ESTUDIANTE', name='rol_usuario'), nullable=False)
    
    estudiante = db.relationship('Estudiante', backref='usuario', uselist=False)
    docente = db.relationship('Docente', backref='usuario', uselist=False)

    def set_password(self, password):
        self.contraseña = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contraseña, password)

class Estudiante(db.Model):
    __tablename__ = 'estudiante'
    id_estudiante = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    expedicion = db.Column(db.String(100), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    paterno = db.Column(db.String(100), nullable=False)
    materno = db.Column(db.String(100))
    fecha_nac = db.Column(db.Date)
    direccion = db.Column(db.String(255))
    genero = db.Column(db.Enum('MASCULINO', 'FEMENINO', name='genero_estudiante'),nullable=False)
    nombre_padre = db.Column(db.String(100), nullable=True)
    telefono_padre = db.Column(db.String(50), nullable=True)
    nombre_madre = db.Column(db.String(100), nullable=True)
    telefono_madre = db.Column(db.String(50), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False)
    
    foto = db.Column(db.String(255), nullable=True)

    inscripciones = db.relationship('Inscripcion', backref='estudiante_rel', lazy=True)

class Docente(db.Model):
    __tablename__ = 'docente'
    id_docente = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    expedicion = db.Column(db.String(100), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    paterno = db.Column(db.String(100), nullable=False)
    materno = db.Column(db.String(100))
    especialidad = db.Column(db.String(100))
    grado_academico = db.Column(db.String(100), nullable=True)
    fecha_ingreso_ue = db.Column(db.Date, nullable=True)
    fecha_titulacion = db.Column(db.Date, nullable=True)
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(120), unique=True)
    foto = db.Column(db.String(255), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False)
    asignaciones = db.relationship('Asignacion', backref='docente_rel', lazy=True)

class Gestion(db.Model):
    __tablename__ = 'gestion'
    id_gestion = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.String(4), nullable=False)
    estado = db.Column(db.Enum('ACTIVA', 'CERRADA', name='estado_gestion'), nullable=False, default='ACTIVA')
    cursos = db.relationship('Curso', backref='gestion_rel', lazy=True)

class Grado(db.Model):
    __tablename__ = 'grado'
    id_grado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    paralelo = db.Column(db.String(1), nullable=False)
    cursos = db.relationship('Curso', backref='grado_rel', lazy=True)

class Curso(db.Model):
    __tablename__ = 'curso'
    id_curso = db.Column(db.Integer, primary_key=True)
    id_grado = db.Column(db.Integer, db.ForeignKey('grado.id_grado'), nullable=False)
    id_gestion = db.Column(db.Integer, db.ForeignKey('gestion.id_gestion'), nullable=False)
    inscripciones = db.relationship('Inscripcion', backref='curso_rel', lazy=True)
    asignaciones = db.relationship('Asignacion', backref='curso_rel', lazy=True)

class Materia(db.Model):
    __tablename__ = 'materia'
    id_materia = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    asignaciones = db.relationship('Asignacion', backref='materia_rel', lazy=True)
    notas = db.relationship('Nota', backref='materia_rel', lazy=True)

class Asignacion(db.Model):
    __tablename__ = 'asignacion'
    id_asignacion = db.Column(db.Integer, primary_key=True)
    id_curso = db.Column(db.Integer, db.ForeignKey('curso.id_curso'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    id_docente = db.Column(db.Integer, db.ForeignKey('docente.id_docente'), nullable=False)

class Inscripcion(db.Model):
    __tablename__ = 'inscripcion'
    id_inscripcion = db.Column(db.Integer, primary_key=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id_estudiante'), nullable=False)
    id_curso = db.Column(db.Integer, db.ForeignKey('curso.id_curso'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.relationship('Nota', backref='inscripcion_rel', lazy=True)
    documentos = db.relationship('Documentacion', backref='inscripcion_rel', lazy=True)

class Nota(db.Model):
    __tablename__ = 'notas'
    id_nota = db.Column(db.Integer, primary_key=True)
    id_inscripcion = db.Column(db.Integer, db.ForeignKey('inscripcion.id_inscripcion'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    primer_trimestre = db.Column(db.Numeric(5, 2))
    segundo_trimestre = db.Column(db.Numeric(5, 2))
    tercer_trimestre = db.Column(db.Numeric(5, 2))
    promedio_final = db.Column(db.Numeric(5, 2))

class Documentacion(db.Model):
    __tablename__ = 'documentacion'
    id_documento = db.Column(db.Integer, primary_key=True)
    id_inscripcion = db.Column(db.Integer, db.ForeignKey('inscripcion.id_inscripcion'), nullable=False)
    tipo_documento = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.Enum('ENTREGADO', 'PENDIENTE', name='estado_documento'), nullable=False, default='PENDIENTE')

class Horario(db.Model):
    """Representa una clase específica programada en el tiempo."""
    __tablename__ = 'horarios'

    id = db.Column(db.Integer, primary_key=True)
    
    id_curso = db.Column(db.Integer, db.ForeignKey('curso.id_curso'), nullable=False)
    id_docente = db.Column(db.Integer, db.ForeignKey('docente.id_docente'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)

    dia_semana = db.Column(
        Enum('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', name='dia_semana_enum'), 
        nullable=False
    )
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    aula = db.Column(db.String(20), nullable=True)

    curso = db.relationship('Curso', backref='horarios')
    docente = db.relationship('Docente', backref='horarios')
    materia = db.relationship('Materia', backref='horarios')

    __table_args__ = (
        db.UniqueConstraint('id_curso', 'dia_semana', 'hora_inicio', name='_curso_dia_hora_unico'),
    )

    def __repr__(self):
        return f'<Clase: {self.materia.nombre} con {self.docente.nombre} el {self.dia_semana}>'