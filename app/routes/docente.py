from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Asignacion, Nota, Inscripcion, Estudiante, Curso, Materia
from ..decorators import docente_required
from sqlalchemy import distinct 
from flask import make_response, render_template_string
from xhtml2pdf import pisa
import io
from io import BytesIO
import os

docente_bp = Blueprint('docente', __name__)

@docente_bp.route('/dashboard')
@login_required
@docente_required
def dashboard():
    if not current_user.docente:
        flash('Tu usuario de docente no está correctamente configurado. Contacta al administrador.', 'danger')
        return redirect(url_for('auth.logout'))

    docente_id = current_user.docente.id_docente

    asignaciones = Asignacion.query.filter_by(id_docente=docente_id).all()

    cursos = list(set(a.curso_rel for a in asignaciones))

    return render_template('docente/dashboard.html', asignaciones=asignaciones, cursos=cursos)
@docente_bp.route('/registrar_notas/<int:id_asignacion>/<int:id_inscripcion>', methods=['GET', 'POST'])
@login_required
@docente_required
def registrar_notas(id_asignacion, id_inscripcion):

    print(f"--- DEPURACIÓN EN REGISTRAR NOTAS ---")
    print(f"ID de Asignación de la URL: {id_asignacion}")
    print(f"ID de Docente Logueado: {current_user.docente.id_docente}")
 
    asignacion = Asignacion.query.get_or_404(id_asignacion)
    print(f"ID de Docente en la Asignación de la BD: {asignacion.id_docente}")
    
    if asignacion.id_docente != current_user.docente.id_docente:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('docente.dashboard'))
    inscripcion = Inscripcion.query.get_or_404(id_inscripcion)
    materia = asignacion.materia_rel

    nota = Nota.query.filter_by(id_inscripcion=id_inscripcion, id_materia=materia.id_materia).first()
    
    if request.method == 'POST':
 
        if not nota:
            nota = Nota(id_inscripcion=id_inscripcion, id_materia=materia.id_materia)
            db.session.add(nota)

        p1 = request.form.get('primer_trimestre')
        p2 = request.form.get('segundo_trimestre')
        p3 = request.form.get('tercer_trimestre')

        nota.primer_trimestre = float(p1) if p1 else None
        nota.segundo_trimestre = float(p2) if p2 else None
        nota.tercer_trimestre = float(p3) if p3 else None
 
        if nota.primer_trimestre is not None and nota.segundo_trimestre is not None and nota.tercer_trimestre is not None:
            nota.promedio_final = (nota.primer_trimestre + nota.segundo_trimestre + nota.tercer_trimestre) / 3
        else:
            nota.promedio_final = None 

        db.session.commit()
        flash('Notas guardadas exitosamente.', 'success')
        return redirect(url_for('docente.listar_notas', id_asignacion=id_asignacion))

    return render_template('docente/registrar_notas.html', 
                           inscripcion=inscripcion,
                           materia=materia,
                           nota=nota)

@docente_bp.route('/listar_notas/<int:id_asignacion>')
@login_required
@docente_required
def listar_notas(id_asignacion):
    asignacion = Asignacion.query.get_or_404(id_asignacion)
  
    if asignacion.id_docente != current_user.docente.id_docente:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('docente.dashboard'))

    curso = asignacion.curso_rel
    materia = asignacion.materia_rel

    inscripciones = Inscripcion.query.filter_by(id_curso=curso.id_curso).all()

    return render_template('docente/listar_notas.html', 
                           inscripciones=inscripciones, 
                           materia=materia,
                           curso=curso)

@docente_bp.route('/editar-nota/<int:id_nota>', methods=['GET', 'POST'])
@login_required
def editar_nota(id_nota):
    """Muestra un formulario para editar una nota específica."""
    nota = Nota.query.get_or_404(id_nota)
  
    if nota.inscripcion_rel.curso_rel.id_docente != current_user.id:
        flash('No tienes permiso para editar esta nota.', 'danger')
        return redirect(url_for('docente.dashboard'))

    if request.method == 'POST':

        primer_trimestre = request.form.get('primer_trimestre')
        segundo_trimestre = request.form.get('segundo_trimestre')
        tercer_trimestre = request.form.get('tercer_trimestre')

        nota.primer_trimestre = primer_trimestre
        nota.segundo_trimestre = segundo_trimestre
        nota.tercer_trimestre = tercer_trimestre

        try:
            pt = float(primer_trimestre or 0)
            st = float(segundo_trimestre or 0)
            tt = float(tercer_trimestre or 0)
            nota.promedio_final = (pt + st + tt) / 3
        except (ValueError, TypeError):
            nota.promedio_final = 0.0

        db.session.commit()
        flash('Nota actualizada exitosamente.', 'success')

        return redirect(url_for('docente.registrar_notas', id_curso=nota.inscripcion_rel.id_curso, id_materia=nota.id_materia))

    return render_template('docente/editar_nota.html', nota=nota)

@docente_bp.route('/ver_notas/<int:id_inscripcion>/<int:id_materia>')
@login_required
@docente_required
def ver_notas_estudiante(id_inscripcion, id_materia):
 
    inscripcion = Inscripcion.query.get_or_404(id_inscripcion)
    
    nota = Nota.query.filter_by(id_inscripcion=id_inscripcion, id_materia=id_materia).first()

    asignacion = Asignacion.query.filter_by(
        id_curso=inscripcion.id_curso, 
        id_materia=id_materia, 
        id_docente=current_user.docente.id_docente
    ).first()

    if not asignacion:
        abort(403) 

    return render_template('docente/ver_notas_estudiante.html',
                           inscripcion=inscripcion,
                           nota=nota,
                           materia=asignacion.materia_rel)


@docente_bp.route('/lista_estudiantes/<int:id_curso>')
@login_required
@docente_required
def lista_estudiantes_curso(id_curso):

    curso = Curso.query.get_or_404(id_curso)
    asignaciones = Asignacion.query.filter_by(id_curso=id_curso).all()

    if not any(a.id_docente == current_user.docente.id_docente for a in asignaciones):
        flash('No tienes permiso para ver la lista de este curso.', 'danger')
        return redirect(url_for('docente.dashboard'))

    inscripciones = Inscripcion.query.filter_by(id_curso=id_curso).all()
 
    estudiantes_data = []
    for inscripcion in inscripciones:
        estudiante = inscripcion.estudiante_rel
        notas_por_asignatura = []
        
        for asignacion in asignaciones:
            nota = Nota.query.filter_by(
                id_inscripcion=inscripcion.id_inscripcion, 
                id_materia=asignacion.id_materia
            ).first()
            notas_por_asignatura.append({'materia': asignacion.materia_rel, 'nota': nota})

        estudiantes_data.append({
            'estudiante': estudiante,
            'inscripcion': inscripcion,  
            'notas': notas_por_asignatura
        })

    return render_template('docente/lista_estudiantes_curso.html', 
                           curso=curso,
                           asignaciones=asignaciones,
                           estudiantes_data=estudiantes_data)

@docente_bp.route('/descargar_boletin/<int:id_curso>')
@login_required
@docente_required
def descargar_boletin_curso(id_curso):

    curso = Curso.query.get_or_404(id_curso)
    asignaciones = Asignacion.query.filter_by(id_curso=id_curso).all()

    if not any(a.id_docente == current_user.docente.id_docente for a in asignaciones):
        flash('No tienes permiso para descargar este boletín.', 'danger')
        return redirect(url_for('docente.dashboard'))

    inscripciones = Inscripcion.query.filter_by(id_curso=id_curso).all()
    
    estudiantes_data = []
    for inscripcion in inscripciones:
        estudiante = inscripcion.estudiante_rel
        notas_por_asignatura = []
        for asignacion in asignaciones:
            nota = Nota.query.filter_by(id_inscripcion=inscripcion.id_inscripcion, id_materia=asignacion.id_materia).first()
            notas_por_asignatura.append({'materia': asignacion.materia_rel, 'nota': nota})
        estudiantes_data.append({'estudiante': estudiante, 'notas': notas_por_asignatura})

    html = render_template('docente/reporte_boletin_pdf.html', 
                           curso=curso,
                           asignaciones=asignaciones,
                           estudiantes_data=estudiantes_data)


    pdf = io.BytesIO() 
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0) 

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=boletin_{curso.grado_rel.nombre}_{curso.grado_rel.paralelo}.pdf'
    
    return response

@docente_bp.route('/boletin/materia/<int:id_materia>')
@login_required
def boletin_por_materia(id_materia):

    print(f"--- DEPURACIÓN DE BOLETÍN ---")
    print(f"ID del Docente Logueado: {current_user.id}")
    print(f"ID de la Materia Seleccionada: {id_materia}")
    
    asignacion = Asignacion.query.filter_by(id_materia=id_materia, id_docente=current_user.id).first()
    print(f"¿Se encontró la asignación? {'Sí' if asignacion else 'NO'}")
    if asignacion:
        print(f"ID de la asignación encontrada: {asignacion.id_asignacion}")
    print(f"--- FIN DE LA DEPURACIÓN ---")

    if not asignacion:
        flash('No puedes ver las calificaciones de esta materia.', 'danger')
        return redirect(url_for('docente.dashboard'))

@docente_bp.route('/lista_simple_estudiantes/<int:id_curso>')
@login_required
@docente_required
def lista_simple_estudiantes(id_curso):
    
    curso = Curso.query.get_or_404(id_curso)
    asignaciones = Asignacion.query.filter_by(id_curso=id_curso).all()
    
    if not any(a.id_docente == current_user.docente.id_docente for a in asignaciones):
        flash('No tienes permiso para ver la lista de este curso.', 'danger')
        return redirect(url_for('docente.dashboard'))

    inscripciones = db.session.query(Inscripcion)\
        .join(Estudiante, Inscripcion.id_estudiante == Estudiante.id_estudiante)\
        .filter(Inscripcion.id_curso == id_curso)\
        .order_by(Estudiante.paterno, Estudiante.materno, Estudiante.nombre)\
        .all()

    return render_template('docente/lista_simple_estudiantes.html', 
                           curso=curso, 
                           inscripciones=inscripciones)

@docente_bp.route('/seleccionar_curso_para_lista')
@login_required
@docente_required
def seleccionar_curso_para_lista():

    if not current_user.docente:
        flash('Tu usuario de docente no está correctamente configurado.', 'danger')
        return redirect(url_for('auth.logout'))

    docente_id = current_user.docente.id_docente

    cursos_ids_query = db.session.query(distinct(Asignacion.id_curso)).filter_by(id_docente=docente_id)
    cursos_ids = [c[0] for c in cursos_ids_query.all()]
  
    cursos = Curso.query.filter(Curso.id_curso.in_(cursos_ids)).all()

    return render_template('docente/seleccionar_curso_lista.html', cursos=cursos)

@docente_bp.route('/reporte/materia/<int:id_materia>')
@login_required
def descargar_reporte_materia(id_materia):
  
    print(f"--- DEPURACIÓN DE REPORTE ---")
    print(f"ID del Docente Logueado: {current_user.docente.id_docente}")
    print(f"ID de la Materia Seleccionada: {id_materia}")
  
    materia = Materia.query.get_or_404(id_materia)
    asignacion = Asignacion.query.filter_by(id_materia=id_materia, id_docente=current_user.docente.id_docente).first()
    if not asignacion:
        flash('No tienes permiso para generar un reporte de esta materia.', 'danger')
        return redirect(url_for('docente.dashboard'))

    curso = asignacion.curso_rel
    id_curso = curso.id_curso

    estudiantes_inscritos = Inscripcion.query.filter_by(id_curso=id_curso).all()
    print(f"Se encontraron {len(estudiantes_inscritos)} estudiantes en el curso {curso.grado_rel.nombre} {curso.grado_rel.paralelo}")

    estudiantes_data = []
    for estudiante in estudiantes_inscritos:

        nota = Nota.query.filter_by(id_inscripcion=estudiante.id_inscripcion, id_materia=id_materia).first()

        promedio = 0
        if nota:
            notas_valores = [nota.primer_trimestre or 0, nota.segundo_trimestre or 0, nota.tercer_trimestre or 0]
            promedio = sum(notas_valores) / len(notas_valores)
        
        estudiantes_data.append({
            'estudiante': estudiante,
            'nota1': nota.primer_trimestre if nota else 'S/N',
            'nota2': nota.segundo_trimestre if nota else 'S/N',
            'nota3': nota.tercer_trimestre if nota else 'S/N',
            'promedio': f"{promedio:.2f}" if promedio > 0 else 'S/N'
        })

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_url = os.path.join(project_root, 'static', 'images', 'logo_reporte.jpg')
    html = render_template('docente/reporte_materia.html', materia=materia, estudiantes=estudiantes_data, logo_url=logo_url)

    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_{materia.nombre}.pdf'
    return response