from flask import render_template
from app.main import bp

@bp.route('/')
def index():
    """Home page"""
    return render_template('main/index.html')

