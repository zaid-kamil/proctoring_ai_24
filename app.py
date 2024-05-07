from flask import Flask, render_template, request, redirect, flash, send_file, session
from werkzeug.utils import secure_filename
import os
from database import *
from datetime import datetime
import json
from aiproctor import Proctor
from threading import Thread

app = Flask(__name__)
app.secret_key = 'random string'

proctoring_instance = None

@app.route('/')
def index():
    return render_template('index.html')

# register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        name = request.form.get('name')
        surname = request.form.get('surname')
        if not username or not password or not email or not name or not surname:
            flash('Please fill all fields', 'danger')
            return redirect('/register')
        db = opendb()
        if db.query(User).filter(User.username == username).first():
            flash('Username already exists' , 'danger')
            return redirect('/register')
        if db.query(User).filter(User.email == email).first():
            flash('Email already exists', 'danger')
            return redirect('/register')
        user = User(username=username, password=password, email=email, name=name, surname=surname)
        save(user)
        flash('User registered successfully', 'success')
        return redirect('/login')
    return render_template('register.html')

# login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please fill all fields', 'danger')
            return redirect('/login')
        db = opendb()
        user = db.query(User).filter(User.username == username, User.password == password).first()
        if user:
            flash('Logged in successfully', 'success')
            # session stores => userid, username, role, name, surname, email, is_banned, isauth
            session['userid'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            session['surname'] = user.surname
            session['email'] = user.email
            session['is_banned'] = user.is_banned
            session['isauth'] = True
            return redirect('/dashboard')
        flash('Invalid credentials', 'danger')
        return redirect('/login')
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# student dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('isauth'):
        return redirect('/login')
    db = opendb()
    # load exams
    exams = db.query(Exam).all()
    attempts = db.query(Attempt).filter(Attempt.user_id == 1).all()
    for attempt in attempts:
        attempt.exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    for exam in exams:
        exam.attempt = db.query(Attempt).filter(Attempt.user_id == 1, Attempt.exam_id == exam.id).first()
    return render_template('dashboard.html', exams=exams, attempts=attempts)

# admin dashboard
@app.route('/admin')
def admin():
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    # load exams
    users = db.query(User).all()
    exams = db.query(Exam).all()
    attempts = db.query(Attempt).all()
    proctorlogs = db.query(ProctorLog).all()
    questions = db.query(Question).all()
    user_count = len(users)
    exam_count = len(exams)
    attempt_count = len(attempts)
    proctorlog_count = len(proctorlogs)
    question_count = len(questions)
    for attempt in attempts:
        attempt.exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
        attempt.user = db.query(User).filter(User.id == attempt.user_id).first()
    for proctorlog in proctorlogs:
        proctorlog.exam = db.query(Exam).filter(Exam.id == proctorlog.exam_id).first()
        proctorlog.user = db.query(User).filter(User.id == proctorlog.user_id).first()
    
    print(f'User count: {user_count}, Exam count: {exam_count}, Attempt count: {attempt_count}, Proctorlog count: {proctorlog_count}, Question count: {question_count}')
    return render_template('admin.html', 
                           exams=exams,  users=users, 
                           attempts=attempts, proctorlogs=proctorlogs, 
                           questions=questions,user_count=user_count,
                           exam_count=exam_count,attempt_count=attempt_count,
                           proctorlog_count=proctorlog_count,  question_count=question_count)

# add new exam
@app.route('/add_exam', methods=['POST'])
def add_exam():
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    name = request.form.get('name')
    duration = request.form.get('duration')
    passing_score = request.form.get('passing_score')
    total_score = request.form.get('total_score')
    if not name or not duration or not passing_score or not total_score:
        flash('Please fill all fields', 'danger')
        return redirect('/admin')
    exam = Exam(name=name, duration=duration, passing_score=passing_score, total_score=total_score, created_at=datetime.now())
    save(exam)
    flash('Exam added successfully', 'success')
    return redirect('/admin')

# add new question
@app.route('/add_question', methods=['POST'])
def add_question():
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    exam_id = request.form.get('exam_id')
    question = request.form.get('question')
    option_a = request.form.get('option_a')
    option_b = request.form.get('option_b')
    option_c = request.form.get('option_c')
    option_d = request.form.get('option_d')
    correct_option = request.form.get('correct_option')
    marks = request.form.get('marks', 10)
    if not exam_id or not question or not option_a or not option_b or not option_c or not option_d or not correct_option or not marks:
        flash('Please fill all fields', 'danger')
        return redirect('/admin')
    question = Question(exam_id=exam_id, question=question, option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d, correct_option=correct_option, marks=marks, created_at=datetime.now())
    save(question)
    flash('Question added successfully', 'success')
    return redirect('/admin')

# add new user
@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    name = request.form.get('name')
    surname = request.form.get('surname')
    role = request.form.get('role')
    if not username or not password or not email or not name or not surname or not role:
        flash('Please fill all fields', 'danger')
        return redirect('/admin')
    user = User(username=username, password=password, email=email, name=name, surname=surname, role=role)
    save(user)
    flash('User added successfully', 'success')
    return redirect('/admin')

# delete exam
@app.route('/delete_exam/<int:id>') 
def delete_exam(id):
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    exam = db.query(Exam).filter(Exam.id == id).first()
    exam.is_deleted = True
    save(exam)
    flash('Exam deleted successfully', 'success')
    return redirect('/admin')

# delete question
@app.route('/delete_question/<int:id>')
def delete_question(id):
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    question = db.query(Question).filter(Question.id == id).first()
    question.is_deleted = True
    save(question)
    flash('Question deleted successfully', 'success')
    return redirect('/admin')

# delete user
@app.route('/delete_user/<int:id>')
def delete_user(id):
    if not session.get('isauth'):
        return redirect('/login')
    if session.get('role') != 'admin':
        return redirect('/login')
    db = opendb()
    user = db.query(User).filter(User.id == id).first()
    user.is_deleted = True
    save(user)
    flash('User deleted successfully', 'success')
    return redirect('/admin')

# start exam
@app.route('/exam/<int:id>')
def exam(id):
    global proctoring_instance
    if not session.get('isauth'):
        return redirect('/login')
    db = opendb()
    exam = db.query(Exam).filter(Exam.id == id).first()
    # create attempt
    if not exam:
        flash('Exam not found', 'danger')
        return redirect('/dashboard')
    # create an attempt entry if not exists and last attempt is 1 hour ago
    attempt = db.query(Attempt).filter(Attempt.user_id == 1, Attempt.exam_id == id).first()
    if not attempt:
        attempt = Attempt(user_id=1, exam_id=id, created_at=datetime.now())
        save(attempt)
    else:
        if (datetime.now() - attempt.created_at).seconds > 100:
            attempt = Attempt(user_id=1, exam_id=id, created_at=datetime.now())
            save(attempt)
        else:
            flash('You have already attempted this exam', 'danger')
            return redirect('/dashboard')
    total_questions = db.query(Question).filter(Question.exam_id == id).count()
    # start proctoring
    last_attempt_id = db.query(Attempt).filter(Attempt.user_id == 1, Attempt.exam_id == id).order_by(Attempt.id.desc()).first().id
    proctoring_instance = Proctor(
        user_id=session.get('userid'), 
        exam_id=id, 
        attempt_id=last_attempt_id, 
        duration=exam.duration,
    )
    print('Starting proctoring')
    thread = Thread(target=proctoring_instance.start_proctoring)
    thread.start()
    print('Proctoring started')
    return render_template('exam.html', exam=exam, total_questions=total_questions, video_path=proctor.video_save_path)

# load exam question
@app.route('/exam/<int:exam_id>/question/<int:question_id>', methods=['GET', 'POST'])
def exam_question(exam_id, question_id):
    
    db = opendb()
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    attempt = db.query(Attempt).filter(Attempt.user_id == 1, Attempt.exam_id == exam_id).first()
    question = db.query(Question).filter(Question.id == question_id).first()
    if request.method == 'POST':
        answer = request.form.get('answer')
        if not answer:
            flash('Please select an answer', 'danger')
            return redirect(f'/exam/{exam_id}/question/{question_id}')
        # save answer
        ans = Answer(user_id=1, exam_id=exam_id, question_id=question_id, attempt_id=attempt.id, answer=answer, created_at=datetime.now())
        save(ans)
        # redirect to next question
        next_question = db.query(Question).filter(Question.exam_id == exam_id, Question.id > question_id).first()
        if next_question:
            return redirect(f'/exam/{exam_id}/question/{next_question.id}')
        else:
            return redirect('/dashboard')
    
    return json.dumps({
        'question': question.question, 
        'option_a': question.option_a, 
        'option_b': question.option_b, 
        'option_c': question.option_c, 
        'option_d': question.option_d,
        'marks': question.marks,
        'exam_id': exam_id, 
        'question_id': question_id, 
        'attempt_id': attempt.id}
    )


@app.route('/exam/<int:exam_id>/save', methods=['GET', 'POST'])
def finish_exam(exam_id):
    if proctoring_instance:
        proctoring_instance.status = 2

    db = opendb()
    attempt = db.query(Attempt).filter(Attempt.user_id == 1, Attempt.exam_id == exam_id).first()
    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    total_marks = 0
    for ans in answers:
        question = db.query(Question).filter(Question.id == ans.question_id).first()
        if ans.answer == question.correct_option:
            total_marks += question.marks
    attempt.score = total_marks
    save(attempt)
    path = request.args.get('path')
    proctorlog = ProctorLog(
        user_id=session.get('userid'), 
        exam_id=exam_id, 
        attempt_id=attempt.id, 
        recording=path, 
        status=1,
        created_at=datetime.now()
    )
    save(proctorlog)
    return redirect('/dashboard')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
 