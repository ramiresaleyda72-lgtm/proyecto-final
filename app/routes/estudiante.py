from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from ..models import db, Inscripcion, Nota, Curso, Gestion, Asignacion, Materia
from ..decorators import estudiante_required
import tempfile
import os
from xhtml2pdf import pisa

estudiante_bp = Blueprint('estudiante', __name__)

@estudiante_bp.route('/dashboard')
@login_required
@estudiante_required
def dashboard():
  
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    if not gestion_activa:
        flash('No hay una gestión académica activa.', 'info')
        return render_template('estudiante/dashboard.html', inscripcion=None)

 
    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.estudiante.id_estudiante
    ).join(Curso).filter(Curso.id_gestion == gestion_activa.id_gestion).first()

    if not inscripcion:
        return render_template('estudiante/dashboard.html', inscripcion=None)
    asignaciones = Asignacion.query.filter_by(id_curso=inscripcion.id_curso).all()

    return render_template('estudiante/dashboard.html', inscripcion=inscripcion, asignaciones=asignaciones)

@estudiante_bp.route('/inscribirse', methods=['GET', 'POST'])
@login_required
@estudiante_required
def inscribirse():
    
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    if not gestion_activa:
        flash('No hay una gestión académica activa para inscribirse.', 'warning')
        return redirect(url_for('estudiante.dashboard'))

    inscripcion_existente = Inscripcion.query.filter_by(
        id_estudiante=current_user.estudiante.id_estudiante
    ).join(Curso).filter(Curso.id_gestion == gestion_activa.id_gestion).first()

    cursos_disponibles = Curso.query.filter_by(id_gestion=gestion_activa.id_gestion).all()

    if request.method == 'POST':
        id_curso = request.form.get('id_curso')
        if not id_curso:
            flash('Debe seleccionar un curso.', 'danger')
            return redirect(url_for('estudiante.inscribirse'))
        
        nueva_inscripcion = Inscripcion(
            id_estudiante=current_user.estudiante.id_estudiante,
            id_curso=id_curso
        )
        db.session.add(nueva_inscripcion)
        db.session.commit()
        flash('Inscripción realizada con éxito.', 'success')
        return redirect(url_for('estudiante.dashboard'))
      
    return render_template('estudiante/inscribirse.html', 
                           cursos=cursos_disponibles, 
                           ya_inscrito=bool(inscripcion_existente),
                           inscripcion_actual=inscripcion_existente) 

@estudiante_bp.route('/notas')
@login_required
@estudiante_required
def ver_notas():
   
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    if not gestion_activa:
        flash('No hay una gestión activa para mostrar notas.', 'info')
        return redirect(url_for('estudiante.dashboard'))

    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.estudiante.id_estudiante
    ).join(Curso).filter(Curso.id_gestion == gestion_activa.id_gestion).first()

    if not inscripcion:
        flash('Aún no te has inscrito en ningún curso para la gestión actual.', 'warning')
        return redirect(url_for('estudiante.inscribirse'))
    
    notas = Nota.query.filter_by(id_inscripcion=inscripcion.id_inscripcion).all()
    
    return render_template('estudiante/ver_notas.html', notas=notas, inscripcion=inscripcion)

@estudiante_bp.route('/descargar_reporte_pdf')
@login_required
@estudiante_required
def descargar_reporte_pdf():
 
    gestion_activa = Gestion.query.filter_by(estado='ACTIVA').first()
    if not gestion_activa:
        flash('No hay una gestión activa para generar un reporte.', 'info')
        return redirect(url_for('estudiante.dashboard'))

    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.estudiante.id_estudiante
    ).join(Curso).filter(Curso.id_gestion == gestion_activa.id_gestion).first()

    if not inscripcion:
        flash('No tienes una inscripción activa para generar un reporte.', 'warning')
        return redirect(url_for('estudiante.dashboard'))
        
    notas = Nota.query.filter_by(id_inscripcion=inscripcion.id_inscripcion).join(Materia).order_by(Materia.nombre).all()

    html = render_template('estudiante/reporte_notas_pdf.html', 
                           estudiante=current_user.estudiante, 
                           inscripcion=inscripcion, 
                           notas=notas)

    pdf = pisa.CreatePDF(html) 

    response = make_response(pdf.dest.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_notas_{current_user.estudiante.ci}.pdf'
    
    return response
