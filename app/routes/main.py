from flask import Blueprint, redirect, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    """
    Página de bienvenida principal.
    """
    return render_template('main/welcome.html')

