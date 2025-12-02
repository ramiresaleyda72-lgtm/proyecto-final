# app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import Usuario, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
 
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Usuario.query.filter_by(nombre_usuario=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')

            if user.rol == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            elif user.rol == 'DOCENTE':

                return redirect(url_for('docente.dashboard'))
            elif user.rol == 'ESTUDIANTE':

                return redirect(url_for('estudiante.dashboard'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('nombre_usuario')
        password = request.form.get('password')
        rol = request.form.get('rol')
        
        if not username or not password or not rol:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('auth/register.html')

        if Usuario.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return render_template('auth/register.html')

        if rol == 'ADMIN':
            admin_count = Usuario.query.filter_by(rol='ADMIN').count()
            if admin_count >= 3:
                flash('Se ha alcanzado el límite de 3 administradores. Contacte al administrador principal.', 'warning')
                return render_template('auth/register.html')

        nuevo_usuario = Usuario(nombre_usuario=username, rol=rol)
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/register-admin', methods=['GET', 'POST'])
@login_required
def register_admin():
    if current_user.rol != 'ADMIN':
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username = request.form.get('nombre_usuario')
        password = request.form.get('password')
        
        if not username or not password:
            flash('El nombre de usuario y la contraseña son obligatorios.', 'danger')
            return render_template('auth/register_admin.html')

        if Usuario.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')

        admin_count = Usuario.query.filter_by(rol='ADMIN').count()
        if admin_count >= 3:
            flash('Ya existe el máximo de 3 administradores. No se pueden crear más cuentas.', 'warning')
            return render_template('auth/register_admin.html')

        nuevo_admin = Usuario(nombre_usuario=username, rol='ADMIN')
        nuevo_admin.set_password(password)

        db.session.add(nuevo_admin)
        db.session.commit()

        flash(f'¡Cuenta de administrador "{username}" creada exitosamente!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('auth/register_admin.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))