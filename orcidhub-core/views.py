# NB! Should be disabled in production
from pyinfo import info
from flask import render_template
from application import app

@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)
