from flask import Response, Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random, string
import csv
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AuthCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    department = db.Column(db.String(100), nullable=False)

def generate_code(length=6):
    while True:
        new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not AuthCode.query.filter_by(code=new_code).first():
            return new_code

def purge_expired_codes():
    now = datetime.now()
    AuthCode.query.filter(AuthCode.expires_at < now, AuthCode.used == False).delete()
    db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        code_input = request.form.get('code', '').upper()
        purge_expired_codes()
        code_entry = AuthCode.query.filter_by(code=code_input, used=False).first()
        if code_entry:
            if code_entry.expires_at < datetime.now():
                flash('Code has expired.')
            else:
                code_entry.used = True
                db.session.commit()
                return render_template('register_form.html', code=code_input)
        else:
            flash('Invalid or used code.')
        return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    student_number = request.form['student_number']
    email = request.form['email']
    code = request.form['code']
    department = request.form['department']

    # Check for duplicate registration
    if Registration.query.filter_by(email=email).first():
        flash('This email has already been registered.')
        return redirect(url_for('register'))

    db.session.add(Registration(
        name=name,
        student_number=student_number,
        email=email,
        code=code,
        department=department
    ))

    db.session.commit()

    # Pass department to success page for logo
    return render_template('success.html', name=name, department=department)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        flash('Invalid credentials.')
        return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST' and 'generate_code' in request.form:
        purge_expired_codes()
        code = generate_code()
        auth_code = AuthCode(code=code, expires_at=datetime.now() + timedelta(minutes=2))
        db.session.add(auth_code)
        db.session.commit()
        session['new_code'] = code
        return redirect(url_for('admin'))

    new_codes = []
    if 'new_code' in session:
        new_codes.append(session.pop('new_code'))

    # Pagination: separate pages for codes and registrations
    code_page = request.args.get('code_page', default=1, type=int)
    reg_page = request.args.get('reg_page', default=1, type=int)
    per_page = 10

    # Search filters
    search_code = request.args.get('search_code', '').strip().upper()
    search_reg = request.args.get('search_reg', '').strip().lower()

    # Apply filters to AuthCode
    auth_code_query = AuthCode.query
    if search_code:
        auth_code_query = auth_code_query.filter(AuthCode.code.like(f'%{search_code}%'))
    codes_paginated = auth_code_query.order_by(AuthCode.id.desc()).paginate(page=code_page, per_page=per_page)

    # Apply filters to Registration
    registration_query = Registration.query
    if search_reg:
        registration_query = registration_query.filter(
            (Registration.name.ilike(f'%{search_reg}%')) |
            (Registration.email.ilike(f'%{search_reg}%'))
        )
    regs_paginated = registration_query.order_by(Registration.id.desc()).paginate(page=reg_page, per_page=per_page)

    total_codes = AuthCode.query.count()
    used_codes = AuthCode.query.filter_by(used=True).count()
    unused_codes = total_codes - used_codes
    total_registrations = Registration.query.count()

    return render_template('admin.html',
                           codes=new_codes,
                           codes_paginated=codes_paginated,
                           regs_paginated=regs_paginated,
                           total_codes=total_codes,
                           used_codes=used_codes,
                           unused_codes=unused_codes,
                           total_registrations=total_registrations)

@app.route('/delete-code/<int:code_id>', methods=['POST'])
def delete_code(code_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    code = AuthCode.query.get_or_404(code_id)
    db.session.delete(code)
    db.session.commit()
    flash('Code deleted successfully.')
    return redirect(url_for('admin'))

@app.route('/reset-code/<int:code_id>', methods=['POST'])
def reset_code(code_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    code = AuthCode.query.get_or_404(code_id)
    if code.used:
        code.used = False
        db.session.commit()
        flash('Code has been reset to unused.')
    else:
        flash('Code is already unused.')
    return redirect(url_for('admin'))

@app.route('/extend-code/<int:code_id>', methods=['POST'])
def extend_code(code_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    code = AuthCode.query.get_or_404(code_id)
    code.expires_at += timedelta(minutes=5)
    db.session.commit()
    flash('Code expiry extended by 5 minutes.')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/export-codes')
def export_codes():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Entry Number', 'Code', 'Used', 'Expires At'])

    codes = AuthCode.query.order_by(AuthCode.id).all()
    for code in codes:
        writer.writerow([code.id, code.code, 'Yes' if code.used else 'No', code.expires_at.strftime("%Y-%m-%d %H:%M:%S")])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment;filename=auth_codes_{timestamp}.csv'})

@app.route('/export-registrations')
def export_registrations():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Entry Number', 'Name', 'Student Number', 'Department', 'Email', 'Code'])

    recent_regs = Registration.query.order_by(Registration.id.desc()).limit(10).all()

    for reg in recent_regs:
        writer.writerow([reg.id, reg.name, reg.student_number, reg.department, reg.email, reg.code])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=registrations_{timestamp}.csv'}
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
