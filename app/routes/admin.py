from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Estudiante, Usuario, Gestion, Grado, Curso, Docente, Materia, Asignacion, Inscripcion, Nota, Horario, Documentacion
from ..decorators import admin_required
from flask import jsonify
from datetime import date
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app 
from flask import send_from_directory

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_estudiantes = Estudiante.query.count()
    total_docentes = Usuario.query.filter_by(rol='DOCENTE').count()
    total_cursos = Curso.query.join(Gestion).filter(Gestion.estado == 'ACTIVA').count()
    
    return render_template('admin/dashboard.html', 
                           total_estudiantes=total_estudiantes,
                           total_docentes=total_docentes,
                           total_cursos=total_cursos)

@admin_bp.route('/uploads/fotos_estudiantes/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@admin_bp.route('/estudiantes')
@login_required
@admin_required
def listar_estudiantes():
    estudiantes = Estudiante.query.all()
    return render_template('admin/listar_estudiantes.html', estudiantes=estudiantes)

@admin_bp.route('/estudiante/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_estudiante():
    if request.method == 'POST':

        ci = request.form['ci'].strip()
        expedicion = request.form.get('expedicion', '').strip()
        nombre = request.form['nombre'].strip()
        paterno = request.form['paterno'].strip()
        materno = request.form.get('materno', '').strip()

        fecha_nac_str = request.form.get('fecha_nac')
        fecha_nac = None
        if fecha_nac_str:
            try:
                from datetime import datetime
                fecha_nac = datetime.strptime(fecha_nac_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.crear_estudiante'))

        direccion = request.form.get('direccion', '').strip()
        genero = request.form.get('genero')
        nombre_padre = request.form.get('nombre_padre', '').strip()
        telefono_padre = request.form.get('telefono_padre', '').strip()
        nombre_madre = request.form.get('nombre_madre', '').strip()
        telefono_madre = request.form.get('telefono_madre', '').strip()
  
        username = request.form['username'].strip()
        password = request.form['password']

        foto = request.files.get('foto_estudiante') 
        nombre_foto = None
        
        if foto and foto.filename: 
            filename = secure_filename(foto.filename)
        
            if filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}:
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fotos_estudiantes')

                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
   
                foto.save(os.path.join(upload_folder, filename))
                nombre_foto = filename
            else:
                flash('Formato de foto no válido. Solo se permiten PNG y JPG.', 'danger')
                return redirect(url_for('admin.crear_estudiante'))

        if Estudiante.query.filter_by(ci=ci).first():
            flash('El CI del estudiante ya está registrado.', 'danger')
            return redirect(url_for('admin.crear_estudiante'))
        if Usuario.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('admin.crear_estudiante'))

        nuevo_usuario = Usuario(nombre_usuario=username, rol='ESTUDIANTE')
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.flush() 

        nuevo_estudiante = Estudiante(
            ci=ci, 
            expedicion=expedicion, 
            nombre=nombre, 
            paterno=paterno, 
            materno=materno,
            fecha_nac=fecha_nac,
            direccion=direccion,
            genero=genero,
            nombre_padre=nombre_padre,
            telefono_padre=telefono_padre,
            nombre_madre=nombre_madre,
            telefono_madre=telefono_madre,
            foto=nombre_foto, 
            id_usuario=nuevo_usuario.id
        )
        db.session.add(nuevo_estudiante)
      
        db.session.commit()
        flash('Estudiante creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_estudiantes'))
        
    return render_template('admin/crear_estudiante.html')

@admin_bp.route('/estudiante/editar/<int:id_estudiante>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_estudiante(id_estudiante):
    estudiante = Estudiante.query.get_or_404(id_estudiante)
    usuario = estudiante.usuario

    if request.method == 'POST':
        ci = request.form['ci'].strip()
        expedicion = request.form.get('expedicion', '').strip() 
        nombre = request.form['nombre'].strip()
        paterno = request.form['paterno'].strip()
        materno = request.form.get('materno', '').strip()
        
        fecha_nac_str = request.form.get('fecha_nac')
        fecha_nac = None
        if fecha_nac_str:
            try:
                from datetime import datetime
                fecha_nac = datetime.strptime(fecha_nac_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.editar_estudiante', id_estudiante=id_estudiante))

        direccion = request.form.get('direccion', '').strip()
        genero = request.form.get('genero')
        nombre_padre = request.form.get('nombre_padre', '').strip()
        telefono_padre = request.form.get('telefono_padre', '').strip()
        nombre_madre = request.form.get('nombre_madre', '').strip()
        telefono_madre = request.form.get('telefono_madre', '').strip()

        username = request.form['username'].strip()
        password = request.form.get('password')

        if Estudiante.query.filter(Estudiante.ci == ci, Estudiante.id_estudiante != id_estudiante).first():
            flash('El C.I. ya está registrado por otro estudiante.', 'danger')
            return redirect(url_for('admin.editar_estudiante', id_estudiante=id_estudiante))
        if Usuario.query.filter(Usuario.nombre_usuario == username, Usuario.id != usuario.id).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('admin.editar_estudiante', id_estudiante=id_estudiante))

        estudiante.ci = ci
        estudiante.expedicion = expedicion 
        estudiante.nombre = nombre
        estudiante.paterno = paterno
        estudiante.materno = materno
        estudiante.fecha_nac = fecha_nac
        estudiante.direccion = direccion
        estudiante.genero = genero
        estudiante.nombre_padre = nombre_padre
        estudiante.telefono_padre = telefono_padre
        estudiante.nombre_madre = nombre_madre
        estudiante.telefono_madre = telefono_madre
     
        usuario.nombre_usuario = username
        if password: 
            usuario.set_password(password)
        
        db.session.commit()
        flash('Estudiante actualizado exitosamente.', 'success')
        return redirect(url_for('admin.listar_estudiantes'))
 
    return render_template('admin/editar_estudiante.html', estudiante=estudiante, usuario=usuario)


@admin_bp.route('/estudiante/eliminar/<int:id_estudiante>', methods=['POST'])
@login_required
@admin_required
def eliminar_estudiante(id_estudiante):
    estudiante = Estudiante.query.get_or_404(id_estudiante)
    usuario_a_eliminar = Usuario.query.get(estudiante.id_usuario)
    
    db.session.delete(estudiante)
    db.session.delete(usuario_a_eliminar)
    db.session.commit()
    
    flash('Estudiante eliminado exitosamente.', 'success')
    return redirect(url_for('admin.listar_estudiantes'))


@admin_bp.route('/ver_estudiante/<int:id_estudiante>')
@login_required
@admin_required
def ver_estudiante(id_estudiante):
    estudiante = Estudiante.query.get_or_404(id_estudiante)
    usuario = estudiante.usuario
    
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    inscripcion = None
    if gestion_activa:
        inscripcion = Inscripcion.query.filter_by(
            id_estudiante=estudiante.id_estudiante
        ).join(Curso).filter(Curso.id_gestion == gestion_activa.id_gestion).first()

    return render_template('admin/ver_estudiante.html', 
                           estudiante=estudiante, 
                           usuario=usuario, 
                           inscripcion=inscripcion)

@admin_bp.route('/inscribir_estudiante', methods=['GET', 'POST'])
@login_required
@admin_required
def inscribir_estudiante():
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    if not gestion_activa:
        flash('No hay una gestión activa.', 'warning')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        id_estudiante = request.form.get('id_estudiante')
        id_curso = request.form.get('id_curso')

        if not id_estudiante or not id_curso:
            flash('Debe seleccionar un estudiante y un curso.', 'danger')
            return redirect(url_for('admin.inscribir_estudiante'))

        inscripcion_existente = Inscripcion.query.filter_by(
            id_estudiante=id_estudiante, id_curso=id_curso
        ).first()

        if inscripcion_existente:
            flash('El estudiante ya está inscrito en este curso.', 'warning')
            return redirect(url_for('admin.inscribir_estudiante'))

        nueva_inscripcion = Inscripcion(id_estudiante=id_estudiante, id_curso=id_curso)
        db.session.add(nueva_inscripcion)
        db.session.commit()
        flash('Inscripción realizada con éxito.', 'success')
        return redirect(url_for('admin.inscribir_estudiante'))

    estudiantes = Estudiante.query.order_by(Estudiante.paterno, Estudiante.nombre).all()
    cursos = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion).all()
    return render_template('admin/inscribir_estudiante.html', estudiantes=estudiantes, cursos=cursos)

@admin_bp.route('/docentes')
@login_required
@admin_required
def listar_docentes():
    docentes = Docente.query.all()
    return render_template('admin/listar_docentes.html', docentes=docentes)

@admin_bp.route('/docente/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_docente():
    if request.method == 'POST':

        ci = request.form['ci']
        expedicion = request.form['expedicion']
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form.get('materno')
        telefono = request.form.get('telefono')
        especialidad = request.form.get('especialidad')
        correo = request.form.get('correo')
        

        grado_academico = request.form.get('grado_academico')

        from datetime import datetime
        fecha_ingreso_ue = None
        fecha_ingreso_str = request.form.get('fecha_ingreso_ue')
        if fecha_ingreso_str:
            try:
                fecha_ingreso_ue = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de ingreso inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.crear_docente'))

        fecha_titulacion = None
        fecha_titulacion_str = request.form.get('fecha_titulacion')
        if fecha_titulacion_str:
            try:
                fecha_titulacion = datetime.strptime(fecha_titulacion_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de titulación inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.crear_docente'))

        username = request.form['username']
        password = request.form['password']

        if Docente.query.filter_by(ci=ci).first():
            flash('El CI del docente ya está registrado.', 'danger')
            return redirect(url_for('admin.crear_docente'))
        if Usuario.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('admin.crear_docente'))
        
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'].replace('estudiantes', 'docentes'), filename))
                foto_filename = filename

        nuevo_usuario = Usuario(nombre_usuario=username, rol='DOCENTE')
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.flush()
        foto_filename = None

        nuevo_docente = Docente(
            ci=ci, expedicion=expedicion, nombre=nombre, paterno=paterno, materno=materno, telefono=telefono,
            especialidad=especialidad, correo=correo,
            grado_academico=grado_academico,  
            fecha_ingreso_ue=fecha_ingreso_ue, 
            fecha_titulacion=fecha_titulacion, 
            foto=foto_filename,
            id_usuario=nuevo_usuario.id
        )
        db.session.add(nuevo_docente)
        db.session.commit()
        
        flash('Docente creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_docentes'))
        
    return render_template('admin/crear_docente.html')

@admin_bp.route('/docente/eliminar/<int:id_docente>', methods=['POST'])
@login_required
@admin_required
def eliminar_docente(id_docente):
    docente = Docente.query.get_or_404(id_docente)
    usuario_a_eliminar = docente.usuario
    
    db.session.delete(docente)
    db.session.delete(usuario_a_eliminar)
    db.session.commit()
    
    flash('Docente eliminado exitosamente.', 'success')
    return redirect(url_for('admin.listar_docentes'))

@admin_bp.route('/docente/editar/<int:id_docente>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_docente(id_docente):
    docente = Docente.query.get_or_404(id_docente)
    usuario_docente = docente.usuario

    if request.method == 'POST':

        ci = request.form['ci']
        expedicion = request.form.get('expedicion')
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form.get('materno')
        telefono = request.form.get('telefono')
        especialidad = request.form.get('especialidad')
        correo = request.form.get('correo')

        grado_academico = request.form.get('grado_academico')

        from datetime import datetime
        fecha_ingreso_ue = None
        fecha_ingreso_str = request.form.get('fecha_ingreso_ue')
        if fecha_ingreso_str:
            try:
                fecha_ingreso_ue = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de ingreso inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.editar_docente', id_docente=id_docente))

        fecha_titulacion = None
        fecha_titulacion_str = request.form.get('fecha_titulacion')
        if fecha_titulacion_str:
            try:
                fecha_titulacion = datetime.strptime(fecha_titulacion_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de titulación inválido. Usa AAAA-MM-DD.', 'danger')
                return redirect(url_for('admin.editar_docente', id_docente=id_docente))

        username = request.form['username']
        password = request.form.get('password')

        if Docente.query.filter(Docente.ci == ci, Docente.id_docente != id_docente).first():
            flash('El C.I. ya está registrado por otro docente.', 'danger')
            return redirect(url_for('admin.editar_docente', id_docente=id_docente))
        if Usuario.query.filter(Usuario.nombre_usuario == username, Usuario.id != usuario_docente.id).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('admin.editar_docente', id_docente=id_docente))

        docente.ci = ci
        docente.expedicion = expedicion
        docente.nombre = nombre
        docente.paterno = paterno
        docente.materno = materno
        docente.telefono = telefono
        docente.especialidad = especialidad
        docente.correo = correo
        docente.grado_academico = grado_academico 
        docente.fecha_ingreso_ue = fecha_ingreso_ue 
        docente.fecha_titulacion = fecha_titulacion 
     
        usuario_docente.nombre_usuario = username
        if password:
            usuario_docente.set_password(password)
        
        db.session.commit()
        flash('Docente actualizado exitosamente.', 'success')
        return redirect(url_for('admin.listar_docentes'))
        
    return render_template('admin/editar_docente.html', docente=docente, usuario=usuario_docente)

@admin_bp.route('/obtener_datos_docente/<int:id_docente>')
@login_required
@admin_required
def obtener_datos_docente(id_docente):
    print(f"--- DEPURACIÓN: Solicitando datos para el docente ID {id_docente} ---")
    try:

        docente = Docente.query.get_or_404(id_docente)
        print(f"--- DEPURACIÓN: Docente encontrado: {docente.nombre} ---")
        
        usuario = docente.usuario
        print(f"--- DEPURACIÓN: Usuario asociado: {usuario.nombre_usuario} ---")

        asignaciones = Asignacion.query.filter_by(id_docente=id_docente).all()
        print(f"--- DEPURACIÓN: Se encontraron {len(asignaciones)} asignaciones ---")

        lista_asignaciones = []
        for asignacion in asignaciones:

            asignacion_data = {
                'curso': f"{asignacion.curso_rel.grado_rel.nombre} '{asignacion.curso_rel.grado_rel.paralelo}'",
                'materia': asignacion.materia_rel.nombre
            }
            lista_asignaciones.append(asignacion_data)

        datos_docente = {
            'ci': docente.ci,
            'nombre': docente.nombre,
            'paterno': docente.paterno,
            'materno': docente.materno,
            'especialidad': docente.especialidad,
            'grado_academico': docente.grado_academico,
            'fecha_ingreso_ue': docente.fecha_ingreso_ue.strftime('%Y-%m-%d') if docente.fecha_ingreso_ue else None,
            'fecha_titulacion': docente.fecha_titulacion.strftime('%Y-%m-%d') if docente.fecha_titulacion else None,
            'telefono': docente.telefono,
            'correo': docente.correo,
            'nombre_usuario': usuario.nombre_usuario,
            'foto': docente.foto,
            'asignaciones': lista_asignaciones
        }
        
        print("--- DEPURACIÓN: Datos a devolver como JSON ---")
        print(datos_docente)
        print("--- FIN DE LA DEPURACIÓN ---")
     
        return jsonify(datos_docente)

    except Exception as e:
        print(f"!!! ERROR EN obtener_datos_docente: {str(e)} !!!")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/gestiones')
@login_required
@admin_required
def listar_gestiones():
    gestiones = Gestion.query.order_by(Gestion.anio.desc()).all()
    return render_template('admin/listar_gestiones.html', gestiones=gestiones)

@admin_bp.route('/gestion/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_gestion():
    if request.method == 'POST':
        anio = request.form['anio']
        

        if Gestion.query.filter_by(anio=anio).first():
            flash(f'Ya existe una gestión para el año {anio}.', 'danger')
            return redirect(url_for('admin.crear_gestion'))

        nueva_gestion = Gestion(anio=anio)
        db.session.add(nueva_gestion)
        db.session.commit()
        flash('Gestión creada exitosamente.', 'success')
        return redirect(url_for('admin.listar_gestiones'))
        
    return render_template('admin/crear_gestion.html')

@admin_bp.route('/gestion/cambiar_estado/<int:id_gestion>', methods=['POST'])
@login_required
@admin_required
def cambiar_estado_gestion(id_gestion):
    """
    Cambia el estado de una gestión entre 'ACTIVA' y 'CERRADA'.
    Asegura que solo una gestión esté activa a la vez.
    """
    gestion = Gestion.query.get_or_404(id_gestion)

    if gestion.estado == 'ACTIVA':

        gestion.estado = 'CERRADA'
        flash(f'La gestión del año {gestion.anio} ha sido cerrada.', 'success')
    else:

        Gestion.query.filter(Gestion.id_gestion != id_gestion).update({'estado': 'CERRADA'})
        gestion.estado = 'ACTIVA'
        flash(f'La gestión del año {gestion.anio} ha sido reabierta.', 'info')
        
    db.session.commit()
    
    return redirect(url_for('admin.listar_gestiones'))

@admin_bp.route('/grados')
@login_required
@admin_required
def listar_grados():
    grados = Grado.query.order_by(Grado.nombre, Grado.paralelo).all()
    return render_template('admin/listar_grados.html', grados=grados)

@admin_bp.route('/grado/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_grado():
    if request.method == 'POST':
        nombre = request.form['nombre']
        paralelo = request.form['paralelo'].upper() 
        if Grado.query.filter_by(nombre=nombre, paralelo=paralelo).first():
            flash(f'El grado {nombre} "{paralelo}" ya está registrado.', 'danger')
            return redirect(url_for('admin.crear_grado'))

        nuevo_grado = Grado(nombre=nombre, paralelo=paralelo)
        db.session.add(nuevo_grado)
        db.session.commit()
        flash('Grado creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_grados'))
        
    return render_template('admin/crear_grado.html')

@admin_bp.route('/grado/editar/<int:id_grado>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_grado(id_grado):
    grado = Grado.query.get_or_404(id_grado)

    if request.method == 'POST':
        nombre = request.form['nombre']
        paralelo = request.form['paralelo'].upper()

        if Grado.query.filter(Grado.nombre == nombre, Grado.paralelo == paralelo, Grado.id_grado != id_grado).first():
            flash(f'El grado {nombre} "{paralelo}" ya está registrado.', 'danger')
            return redirect(url_for('admin.editar_grado', id_grado=id_grado))
        
        grado.nombre = nombre
        grado.paralelo = paralelo
        db.session.commit()
        flash('Grado actualizado exitosamente.', 'success')
        return redirect(url_for('admin.listar_grados'))
        
    return render_template('admin/editar_grado.html', grado=grado)

@admin_bp.route('/grado/eliminar/<int:id_grado>', methods=['POST'])
@login_required
@admin_required
def eliminar_grado(id_grado):
    grado = Grado.query.get_or_404(id_grado)
    db.session.delete(grado)
    db.session.commit()
    flash('Grado eliminado exitosamente.', 'success')
    return redirect(url_for('admin.listar_grados'))

@admin_bp.route('/cursos')
@login_required
@admin_required
def listar_cursos():
    """Muestra una lista de todos los cursos de la gestión activa."""

    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    
    if not gestion_activa:
        flash('No hay una gestión activa. No se pueden mostrar los cursos.', 'warning')
        cursos = []
    else:

        cursos = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion)\
                          .join(Grado)\
                          .order_by(Grado.nombre, Grado.paralelo)\
                          .all()
                          
    return render_template('admin/listar_cursos.html', cursos=cursos)

@admin_bp.route('/curso/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_curso():
    """Crea un nuevo curso (ej: 1ro "A" de la gestión 2024)."""
    if request.method == 'POST':
        id_grado = request.form['id_grado']
        id_gestion = request.form['id_gestion']
        
        if Curso.query.filter_by(id_grado=id_grado, id_gestion=id_gestion).first():
            flash('Este curso para la gestión seleccionada ya existe.', 'danger')
            return redirect(url_for('admin.crear_curso'))

        nuevo_curso = Curso(id_grado=id_grado, id_gestion=id_gestion)
        db.session.add(nuevo_curso)
        db.session.commit()
        flash('Curso creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_cursos'))

    grados = Grado.query.order_by(Grado.nombre, Grado.paralelo).all()
    gestiones = Gestion.query.order_by(Gestion.anio.desc()).all()
    return render_template('admin/crear_curso.html', grados=grados, gestiones=gestiones)

@admin_bp.route('/curso/editar/<int:id_curso>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_curso(id_curso):
    """Edita un curso existente."""
    curso = Curso.query.get_or_404(id_curso)

    if request.method == 'POST':
        id_grado = request.form['id_grado']
        id_gestion = request.form['id_gestion']

        if Curso.query.filter(Curso.id_grado == id_grado, 
                             Curso.id_gestion == id_gestion, 
                             Curso.id_curso != id_curso).first():
            flash('Este curso para la gestión seleccionada ya existe.', 'danger')
            return redirect(url_for('admin.editar_curso', id_curso=id_curso))
        
        curso.id_grado = id_grado
        curso.id_gestion = id_gestion
        db.session.commit()
        flash('Curso actualizado exitosamente.', 'success')
        return redirect(url_for('admin.listar_cursos'))
        
    grados = Grado.query.order_by(Grado.nombre, Grado.paralelo).all()
    gestiones = Gestion.query.order_by(Gestion.anio.desc()).all()
    return render_template('admin/editar_curso.html', curso=curso, grados=grados, gestiones=gestiones)


@admin_bp.route('/curso/eliminar/<int:id_curso>', methods=['POST'])
@login_required
@admin_required
def eliminar_curso(id_curso):
    """Elimina un curso."""
    curso = Curso.query.get_or_404(id_curso)
    db.session.delete(curso)
    db.session.commit()
    flash('Curso eliminado exitosamente.', 'success')
    return redirect(url_for('admin.listar_cursos'))

@admin_bp.route('/materias')
@login_required
@admin_required
def listar_materias():
    materias = Materia.query.order_by(Materia.nombre).all()
    return render_template('admin/listar_materias.html', materias=materias)

@admin_bp.route('/materia/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_materia():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        
        if Materia.query.filter_by(nombre=nombre).first():
            flash('La materia ya está registrada.', 'danger')
            return redirect(url_for('admin.crear_materia'))

        nueva_materia = Materia(nombre=nombre)
        db.session.add(nueva_materia)
        db.session.commit()
        flash('Materia creada exitosamente.', 'success')
        return redirect(url_for('admin.listar_materias'))
        
    return render_template('admin/crear_materia.html')

@admin_bp.route('/materia/editar/<int:id_materia>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_materia(id_materia):
    materia = Materia.query.get_or_404(id_materia)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        
        if Materia.query.filter(Materia.nombre == nombre, Materia.id_materia != id_materia).first():
            flash('La materia ya está registrada.', 'danger')
            return redirect(url_for('admin.editar_materia', id_materia=id_materia))
        
        materia.nombre = nombre
        db.session.commit()
        flash('Materia actualizada exitosamente.', 'success')
        return redirect(url_for('admin.listar_materias'))
        
    return render_template('admin/editar_materia.html', materia=materia)

@admin_bp.route('/materia/eliminar/<int:id_materia>', methods=['POST'])
@login_required
@admin_required
def eliminar_materia(id_materia):
    materia = Materia.query.get_or_404(id_materia)
    db.session.delete(materia)
    db.session.commit()
    flash('Materia eliminada exitosamente.', 'success')
    return redirect(url_for('admin.listar_materias'))

@admin_bp.route('/asignaciones')
@login_required
@admin_required
def listar_asignaciones():

    asignaciones = db.session.query(
        Asignacion, Curso, Materia, Docente
    ).join(Curso).join(Materia).join(Docente).all()
    return render_template('admin/listar_asignaciones.html', asignaciones=asignaciones)

@admin_bp.route('/asignacion/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_asignacion():
    if request.method == 'POST':
        id_curso = request.form['id_curso']
        id_materia = request.form['id_materia']
        id_docente = request.form['id_docente']

        asignacion_existente = Asignacion.query.filter_by(
            id_curso=id_curso, id_materia=id_materia, id_docente=id_docente
        ).first()

        if asignacion_existente:
            flash('Esta asignación ya existe.', 'danger')
            return redirect(url_for('admin.crear_asignacion'))

        nueva_asignacion = Asignacion(
            id_curso=id_curso, 
            id_materia=id_materia, 
            id_docente=id_docente
        )
        db.session.add(nueva_asignacion)
        db.session.commit()
        flash('Asignación (curso activado) creada exitosamente.', 'success')
        return redirect(url_for('admin.listar_asignaciones'))

    cursos = Curso.query.join(Gestion).filter(Gestion.estado == 'ACTIVA').all()
    materias = Materia.query.all()
    docentes = Docente.query.all()
    return render_template('admin/crear_asignacion.html', cursos=cursos, materias=materias, docentes=docentes)

@admin_bp.route('/asignacion/eliminar/<int:id_asignacion>', methods=['POST'])
@login_required
@admin_required
def eliminar_asignacion(id_asignacion):
    asignacion = Asignacion.query.get_or_404(id_asignacion)
    
    db.session.delete(asignacion)
    db.session.commit()
    
    flash('Asignación eliminada exitosamente.', 'success')
    return redirect(url_for('admin.listar_asignaciones'))

@admin_bp.route('/asignacion/editar/<int:id_asignacion>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_asignacion(id_asignacion):
    asignacion = Asignacion.query.get_or_404(id_asignacion)
    
    if request.method == 'POST':
        id_curso = request.form['id_curso']
        id_materia = request.form['id_materia']
        id_docente = request.form['id_docente']

        asignacion_existente = Asignacion.query.filter(
            Asignacion.id_curso == id_curso,
            Asignacion.id_materia == id_materia,
            Asignacion.id_docente == id_docente,
            Asignacion.id_asignacion != id_asignacion
        ).first()

        if asignacion_existente:
            flash('Esta combinación de curso, materia y docente ya está asignada.', 'danger')
            return redirect(url_for('admin.editar_asignacion', id_asignacion=id_asignacion))

        asignacion.id_curso = id_curso
        asignacion.id_materia = id_materia
        asignacion.id_docente = id_docente
        db.session.commit()
        
        flash('Asignación actualizada exitosamente.', 'success')
        return redirect(url_for('admin.listar_asignaciones'))
 
    cursos = Curso.query.join(Gestion).filter(Gestion.estado == 'ACTIVA').all()
    materias = Materia.query.all()
    docentes = Docente.query.all()
    return render_template('admin/editar_asignacion.html', asignacion=asignacion, cursos=cursos, materias=materias, docentes=docentes)

@admin_bp.route('/inscripciones')
@login_required
@admin_required
def listar_inscripciones():

    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    inscripciones = Inscripcion.query.filter(Inscripcion.curso_rel.has(id_gestion=gestion_activa.id_gestion)).all() if gestion_activa else []
    return render_template('admin/listar_inscripciones.html', inscripciones=inscripciones, gestion=gestion_activa)

@admin_bp.route('/inscripcion/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_inscripcion():
    if request.method == 'POST':
        id_estudiante = request.form['id_estudiante']
        id_curso = request.form['id_curso']
   
        if Inscripcion.query.filter_by(id_estudiante=id_estudiante, id_curso=id_curso).first():
            flash('El estudiante ya está inscrito en este curso.', 'danger')
            return redirect(url_for('admin.crear_inscripcion'))

        nueva_inscripcion = Inscripcion(id_estudiante=id_estudiante, id_curso=id_curso)
        db.session.add(nueva_inscripcion)
        db.session.commit()
        flash('Inscripción realizada exitosamente.', 'success')
        return redirect(url_for('admin.listar_inscripciones'))

    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    estudiantes = Estudiante.query.all()
    cursos = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion).all() if gestion_activa else []
    return render_template('admin/crear_inscripcion.html', estudiantes=estudiantes, cursos=cursos)

@admin_bp.route('/inscripcion/eliminar/<int:id_inscripcion>', methods=['POST'])
@login_required
@admin_required
def eliminar_inscripcion(id_inscripcion):
    inscripcion = Inscripcion.query.get_or_404(id_inscripcion)
    db.session.delete(inscripcion)
    db.session.commit()
    flash('Inscripción eliminada exitosamente.', 'success')
    return redirect(url_for('admin.listar_inscripciones'))

@admin_bp.route('/horarios')
@login_required
@admin_required
def listar_horarios():
    """Muestra una lista de todos los horarios, ordenados por día y hora."""
    horarios = Horario.query.order_by(Horario.dia_semana, Horario.hora_inicio).all()
    return render_template('admin/listar_horarios.html', horarios=horarios)

@admin_bp.route('/horario/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_horario():
    """Crea un nuevo bloque de horario."""
    if request.method == 'POST':

        id_curso = request.form['id_curso']
        id_docente = request.form['id_docente']
        id_materia = request.form['id_materia']
        dia_semana = request.form['dia_semana']
    
        hora_inicio_str = request.form['hora_inicio']
        hora_fin_str = request.form['hora_fin']
        
        try:
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        except ValueError:
            flash('Formato de hora inválido. Usa el formato HH:MM.', 'danger')
            return redirect(url_for('admin.crear_horario'))

        aula = request.form.get('aula', '').strip()

        conflicto_curso = Horario.query.filter(
            Horario.id_curso == id_curso,
            Horario.dia_semana == dia_semana,
            Horario.hora_inicio < hora_fin,
            Horario.hora_fin > hora_inicio
        ).first()

        if conflicto_curso:
            flash('Ya existe una clase programada para este curso en ese horario.', 'danger')
            return redirect(url_for('admin.crear_horario'))

        conflicto_docente = Horario.query.filter(
            Horario.id_docente == id_docente,
            Horario.dia_semana == dia_semana,
            Horario.hora_inicio < hora_fin,
            Horario.hora_fin > hora_inicio
        ).first()

        if conflicto_docente:
            flash('El docente ya tiene una clase programada en ese horario.', 'danger')
            return redirect(url_for('admin.crear_horario'))

        nuevo_horario = Horario(
            id_curso=id_curso, 
            id_docente=id_docente, 
            id_materia=id_materia,
            dia_semana=dia_semana, 
            hora_inicio=hora_inicio, 
            hora_fin=hora_fin,
            aula=aula  
        )
        db.session.add(nuevo_horario)
        db.session.commit()
        flash('Horario creado exitosamente.', 'success')
        return redirect(url_for('admin.listar_horarios'))
  
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    cursos = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion).all() if gestion_activa else []
    docentes = Docente.query.all()
    materias = Materia.query.all()
    return render_template('admin/crear_horario.html', cursos=cursos, docentes=docentes, materias=materias)


@admin_bp.route('/horario/editar/<int:id_horario>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_horario(id_horario):
    """Edita un bloque de horario existente."""
    horario = Horario.query.get_or_404(id_horario)

    if request.method == 'POST':
        id_curso = request.form['id_curso']
        id_docente = request.form['id_docente']
        id_materia = request.form['id_materia']
        dia_semana = request.form['dia_semana']
        
        hora_inicio_str = request.form['hora_inicio']
        hora_fin_str = request.form['hora_fin']
        aula = request.form.get('aula', '').strip()

        try:
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        except ValueError:
            flash('Formato de hora inválido. Usa el formato HH:MM.', 'danger')
            return redirect(url_for('admin.editar_horario', id_horario=id_horario))

        conflicto_curso = Horario.query.filter(
            Horario.id_curso == id_curso,
            Horario.dia_semana == dia_semana,
            Horario.hora_inicio < hora_fin,
            Horario.hora_fin > hora_inicio,
            Horario.id != id_horario
        ).first()

        if conflicto_curso:
            flash('Ya existe otra clase programada para este curso en ese horario.', 'danger')
            return redirect(url_for('admin.editar_horario', id_horario=id_horario))

        conflicto_docente = Horario.query.filter(
            Horario.id_docente == id_docente,
            Horario.dia_semana == dia_semana,
            Horario.hora_inicio < hora_fin,
            Horario.hora_fin > hora_inicio,
            Horario.id != id_horario
        ).first()

        if conflicto_docente:
            flash('El docente ya tiene otra clase programada en ese horario.', 'danger')
            return redirect(url_for('admin.editar_horario', id_horario=id_horario))

        horario.id_curso = id_curso
        horario.id_docente = id_docente
        horario.id_materia = id_materia
        horario.dia_semana = dia_semana
        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin
        horario.aula = aula 
        
        db.session.commit()
        flash('Horario actualizado exitosamente.', 'success')
        return redirect(url_for('admin.listar_horarios'))
   
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    cursos = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion).all() if gestion_activa else []
    docentes = Docente.query.all()
    materias = Materia.query.all()
    return render_template('admin/editar_horario.html', horario=horario, cursos=cursos, docentes=docentes, materias=materias)

@admin_bp.route('/horario/eliminar/<int:id_horario>', methods=['POST'])
@login_required
@admin_required
def eliminar_horario(id_horario):
    """Elimina un bloque de horario."""
    horario = Horario.query.get_or_404(id_horario)
    db.session.delete(horario)
    db.session.commit()
    flash('Horario eliminado exitosamente.', 'success')
    return redirect(url_for('admin.listar_horarios'))

@admin_bp.route('/reporte/horario-docente', methods=['GET', 'POST'])
@login_required
@admin_required
def reporte_horario_docente():
    """
    Muestra un formulario para seleccionar un docente y su horario correspondiente.
    """

    docentes = Docente.query.order_by(Docente.paterno, Docente.nombre).all()
    
    selected_docente = None
    horarios = []

    if request.method == 'POST':

        id_docente_seleccionado = request.form.get('id_docente')
        
        if id_docente_seleccionado:

            selected_docente = Docente.query.get(id_docente_seleccionado)
            
            if selected_docente:
                horarios = Horario.query.filter_by(id_docente=id_docente_seleccionado)\
                                     .order_by(Horario.dia_semana, Horario.hora_inicio)\
                                     .all()
    
    return render_template('admin/reporte_horario_docente.html', 
                           docentes=docentes, 
                           selected_docente=selected_docente, 
                           horarios=horarios)

