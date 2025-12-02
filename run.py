import os
from app import create_app
from flask import send_from_directory

app = create_app()

@app.route('/logo')
def serve_logo():
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    logo_directory = os.path.join(project_root, 'static', 'uploads')
    print(f"Buscando el logo en: {logo_directory}")
    return send_from_directory(logo_directory, '16nov.jpg')

@app.route('/test')  
def test_route():
    return "¡Hola! El servidor está cargando el archivo run.py correctamente."

@app.route('/icono')
def serve_icono():
    """
    Esta función sirve el icono del login.
    """
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    icono_directory = os.path.join(project_root, 'static', 'uploads')
    print(f"Buscando el icono en: {icono_directory}") 
    return send_from_directory(icono_directory, 'icono.jpg')


@app.route('/fotos_estudiantes/<filename>')
def serve_foto_estudiante(filename):
    """
    Esta función sirve las fotos de los estudiantes desde su carpeta específica.
    """
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    foto_directory = os.path.join(project_root, 'static', 'uploads', 'fotos_estudiantes')
    print(f"Buscando foto de estudiante en: {foto_directory}") 
    return send_from_directory(foto_directory, filename)

if __name__ == '__main__':
    app.run(debug=True)