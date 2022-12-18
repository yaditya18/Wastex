from __future__ import division
from flask import Flask, render_template, url_for, request, redirect, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

app = Flask(__name__)

app.secret_key = '2' # for flask session


# Use a service account
cred = credentials.Certificate('last-try-a46ac-firebase-adminsdk-cocun-8f50fa0e34.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# pyrebase init
# Your web app's Firebase configuration
firebaseConfig = {
  'apiKey': "AIzaSyB-uEEoMrVqnqKF6tDifJyp14PLJEgrTSY",
  'authDomain': "last-try-a46ac.firebaseapp.com",
  'databaseURL': "https://last-try-a46ac-default-rtdb.asia-southeast1.firebasedatabase.app",
  'projectId': "last-try-a46ac",
  'storageBucket': "last-try-a46ac.appspot.com",
  'messagingSenderId': "338588534442",
  'appId': "1:338588534442:web:b125f5c44fd5762835f2d3",
  'measurementId': "G-G93MM97K41"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()



@app.route('/', methods = ['GET'])
def home_page():
    if 'user' not in session:
        return render_template('home_page.html')
    else:
        return redirect('/logout')










@app.route('/teacher_login', methods = ['GET', 'POST'])
def teacher_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('teacher_login_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        flag_1=flag_2=False
        teacher_emails=db.collection('teacher').stream()
        for teacher_email in teacher_emails:
            if teacher_email.id == email:
                flag_1=True
                # check Password 
                try:
                    teacher_user=auth.sign_in_with_email_and_password(email, password)
                    flag_2=True
                except:
                    flag_2=False
                break
        # check the flags
        if flag_1==False or flag_2==False:
            flash('Incorrect, unverified or non-existent e-mail, division or password...', 'error')
            return redirect('/teacher_login')

        session['user']=email
        session['person_type']='teacher'
        # return redirect('/teacher_dashboard')
        return redirect('/teacher_home')




@app.route('/teacher_signup', methods = ['GET', 'POST'])
def teacher_signup():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('teacher_signup_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        year=request.form['year']

        # check if passwords match
        if password != password2:
            flash('The passwords do not match...', 'error')
            return redirect('/teacher_signup')
        # check length of pass
        if len(password) < 6:
            flash('The password has to be more than 5 characters long...', 'error')
            return redirect('/teacher_signup')
        
        # auth user
        try:
            teacher_user = auth.create_user_with_email_and_password(email, password)
        except:
            flash('This e-mail has already been registered. Please use another e-mail...', 'error')
            return redirect('/teacher_signup')
        # e-mail verification
        # auth.send_email_verification(teacher_user['idToken'])
        # add teacher to db
        db.collection('teacher').document(email).set({
            'name': name,
            'year': year,
            'password': password # firebase auth
        })

        flash('Registration successful! Please check your e-mail for verification and then log in...', 'info')
        return redirect('/teacher_login')

@app.route('/teacher_home', methods=['GET', 'POST'])
def teacher_home():
    if request.method =='GET':
        if 'user' in session and session['person_type'] == 'teacher':
            #get teacher detais
            teacher_details=db.collection('teacher').document(session['user'])
            return render_template('teacher_home.html')

    if request.method =='POST':
        department=request.form['department']
        semester=request.form['semester']
        subject=request.form['subject']
        flag_1=flag_2=flag_3=False
        # check the department is in the database 
        dat_department=db.collection('teacher').document(session['user']).collection('department').stream()
        for dep in dat_department:
            if dep.id==department:
                flag_1=True
        dat_semester=db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').stream()
        for sem in dat_semester:
            if sem.id == semester:
                flag_2=True
        dat_subject=db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').document(semester).collection('subject').stream()
        for sub in dat_subject:
            if sub.id == subject:
                flag_3=True

        if flag_1== False or flag_2== False or flag_3==False:
            flash('Incorrect, unvalid or non-existent department, semester, subject')
            return redirect('/teacher_home')

        session['department']=department
        session['semester']=semester
        session['subject']=subject
        return redirect('/teacher_dashboard')

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method =='GET':
        if 'user' in session and session['person_type']=='teacher':
            teacher_details=db.collection('teacher').document(session['user']).get()
            return render_template('add_subject.html')
        else:
            return redirect('logout')

    if request.method == 'POST':
        # get department semester and subject
        department=request.form['department']
        semester=request.form['semester']
        subject=request.form['subject']
        
        # set the databse in teacher collection
        db.collection('teacher').document(session['user']).collection('department').document(department).set({
            'department':department
        })
        db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').document(semester).set({
            'semester':semester
            })
        db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').document(semester).collection('subject').document(subject).set({
            'subject':subject
        })
        # update the teacher email in student collection
        student_department=db.collection('department').document(department).collection('semester').stream()
        for semesters in student_department:
            semester=semesters.id
            db.collection('department').document(department).collection('semester').document(semester).update({
                'teacher_email': firestore.ArrayUnion([session['user']])
            })

        flash('Subject Added Successfully....')
        return redirect('/teacher_home')


@app.route('/teacher_dashboard', methods = ['GET'])
def teacher_dashboard():
    if 'user' in session and session['person_type'] == 'teacher':
        # get teacher details
        teacher_details = db.collection('teacher').document(session['user']).get()
        # conducted lec count
        lectures = db.collection('teacher').document(session['user']).collection('department').document(session['department']).collection('semester').document(session['semester']).collection('subject').document(session['subject']).collection('lecture').stream()
        lec_conducted_count = 0
        for lecture in lectures:
            lec_conducted_count += 1
        # get all students & lecs
        student_ref = db.collection('department').document(session['department']).collection('semester').document(session['semester']).collection('student').order_by('roll_no')
        lecture_ref = db.collection('teacher').document(session['user']).collection('department').document(session['department']).collection('semester').document(session['semester']).collection('subject').document(session['subject']).collection('lecture').order_by('date')
        students = student_ref.stream()
        lectures = lecture_ref.stream()
        # attendance calculation logic
        attendance = {}
        for student in students:
            attended_bool = []
            lec_attended_count = 0
            for lecture in lectures:
                lec_dict = lecture.to_dict()
                if student.id in lec_dict['student_email']:
                    attended_bool.append(True)
                    lec_attended_count += 1
                else:
                    attended_bool.append(False)
            if lec_conducted_count != 0:
                percentage = int((lec_attended_count/lec_conducted_count)*100)
            else:
                percentage = 0
            attendance[student.id] = [lec_attended_count, percentage, attended_bool]
            lectures = lecture_ref.stream() # needs to be streamed again after every use, reason unkonwn

        students = student_ref.stream() # needs to be streamed again after every use, reason unkonwn
        lectures = lecture_ref.stream() # needs to be streamed again after every use, reason unkonwn
        return render_template('teacher_dashboard_page.html', semester=session['semester'],department=session['department'], subject=session['subject'], teacher_details = teacher_details.to_dict(), lec_conducted_count = lec_conducted_count, attendance = attendance, students = students, lectures = lectures)
    else:
        return redirect('/logout')


@app.route('/confirm_add_edit_lecture', methods=['GET', 'POST'])
def confirm_add_edit_lecture():
    if request.method =='GET':
        if 'user' in session and session['person_type']=='teacher':
            teacher_details=db.collection('teacher').document(session['user']).get()
            return render_template('confirm_add_edit_lecture.html')
        else:
            return redirect('logout')

    if request.method == 'POST':
        department=request.form['department']
        semester=request.form['semester']
        subject=request.form['subject']
        flag_1=flag_2=flag_3=False
        # check the department is in the database 
        dat_department=db.collection('teacher').document(session['user']).collection('department').stream()
        for dep in dat_department:
            if dep.id==department:
                flag_1=True
        dat_semester=db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').stream()
        for sem in dat_semester:
            if sem.id == semester:
                flag_2=True
        dat_subject=db.collection('teacher').document(session['user']).collection('department').document(department).collection('semester').document(semester).collection('subject').stream()
        for sub in dat_subject:
            if sub.id == subject:
                flag_3=True

        if flag_1== False or flag_2== False or flag_3==False:
            flash('Incorrect, unvalid or non-existent department, semester, subject')
            return redirect('/confirm_add_edit_lecture')

        session['lecture_department']=department
        session['lecture_semester']=semester
        session['lecture_subject']=subject
        return redirect('/add_edit_lecture')



@app.route('/add_edit_lecture', methods = ['GET', 'POST'])
def add_edit_lecture():
    if request.method == 'GET':
        if 'user' in session and session['person_type'] == 'teacher':
            # get teacher details
            teacher_details = db.collection('teacher').document(session['user']).get()
            # get students
            students = db.collection('department').document(session['lecture_department']).collection('semester').document(session['lecture_semester']).collection('student').order_by('roll_no').stream()
            count = 0
            for student in students:
                count += 1
            if count == 0:
                flash('No students in division to add lecture...', 'info')
                return redirect('/teacher_home')
            
            students = db.collection('department').document(session['lecture_department']).collection('semester').document(session['lecture_semester']).collection('student').order_by('roll_no').stream()
            return render_template('add_edit_lecture_page.html', lecture_department= session['lecture_department'], lecture_semester=session['lecture_semester'], lecture_subject=session['lecture_subject'],students = students, teacher_details = teacher_details.to_dict())
        else:
            return redirect('/logout')

    if request.method == 'POST':
        # get date and attendance
        date = request.form['date']
        student_emails = request.form.getlist('check-box')
        # edit lecture functionality (delete prev doc)
        lectures = db.collection('teacher').document(session['user']).collection('department').document(session['lecture_department']).collection('semester').document(session['lecture_semester']).collection('subject').document(session['lecture_subject']).collection('lecture').stream()
        for lecture in lectures:
            lec_dict = lecture.to_dict()
            if date == lec_dict['date']:
                db.collection('teacher').document(session['user']).collection('department').document(session['lecture_department']).collection('semester').document(session['lecture_semester']).collection('subject').document(session['lecture_subject']).collection('lecture').document(lecture.id).delete()
                break
        
        lec_doc_ref = db.collection('teacher').document(session['user']).collection('department').document(session['lecture_department']).collection('semester').document(session['lecture_semester']).collection('subject').document(session['lecture_subject']).collection('lecture').document()
        lec_doc_ref.set({
            'date': date,
            'student_email': []
        })
        
        for student_email in student_emails:
            lec_doc_ref.update({
            'student_email': firestore.ArrayUnion([student_email])
            })

        flash('Lecture added/edited successfully...', 'info')
        return redirect('/teacher_home')










@app.route('/student_login', methods = ['GET', 'POST'])
def student_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('student_login_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        department = request.form['department'].upper()
        sem=request.form['semester']

        # check e-mail, div & pass
        flag_1 = flag_2 = flag_3 = flag_4 = False
        div_ref = db.collection('department')
        divs = div_ref.stream()
        # check for div existence
        for div in divs:
            if div.id == department:
                flag_1 = True
                div_student_details = div_ref.document(department).collection('semester').document(sem).collection('student').stream()
                # check for student existence in div
                for student in div_student_details:
                    if student.id == email:
                        flag_2 = True
                        # check pass
                        try:
                            st_user = auth.sign_in_with_email_and_password(email, password)
                            flag_3 = True
                            # e-mail verification check
                            # acc_info = auth.get_account_info(st_user['idToken'])
                            # if acc_info['users'][0]['emailVerified'] == True:
                            flag_4 = True
                        except:
                            flag_3 = False
                        break
                break

        if flag_1 == False or flag_2 == False or flag_3 == False or flag_4 == False:
            flash('Incorrect, unverified or non-existent e-mail, department or password...', 'error')
            return redirect('/student_login')

        session['student_department'] = department
        session['student_semester']=sem
        session['user'] = email
        session['person_type'] = 'student'
        # return redirect('/student_dashboard')
        return redirect('/student_dashboard')



@app.route('/student_signup', methods = ['GET', 'POST'])
def student_signup():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('student_signup_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        department = request.form['department'].upper()
        year = request.form['year']
        sem = request.form['sem']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        # check for same roll no.
        students = db.collection('department').document(department).collection('semester').document(sem).collection('student').stream()
        for student in students:
            st_dict = student.to_dict()
            if st_dict['roll_no'] == roll_no:
                flash(f'Roll no. {roll_no} is already registered for {department}...', 'error')
                return redirect('/student_signup')
        # check if passwords match
        if password != password2:
            flash('The passwords do not match...', 'error')
            return redirect('/student_signup')
        # check length of pass
        if len(password) < 6:
            flash('The password has to be more than 6 characters long...', 'error')
            return redirect('/student_signup')

        # auth user
        try:
            st_user = auth.create_user_with_email_and_password(email, password)
        except:
            flash('This e-mail has already been registered. Please use another e-mail...', 'error')
            return redirect('/student_signup')
        # e-mail verification
        # auth.send_email_verification(st_user['idToken'])
        # check for div
        db.collection('department').document(department).set({
            'department':department
        })
        db.collection('department').document(department).collection('semester').document(sem).set({
            'year': year,
        }, merge = True)
        # add student to db
        db.collection('department').document(department).collection('semester').document(sem).collection('student').document(email).set({
            'name': name,
            'roll_no': roll_no,
            'password':password
        })
        
        flash('Registration successful! Please check your e-mail for verification and then log in...', 'info')
        return redirect('/student_login')



@app.route('/student_dashboard', methods = ['GET', 'POST'])
def student_dashboard():
    if 'user' in session and session['person_type'] == 'student':
        if request.method =='GET':
        # get student data
            div_ref = db.collection('department').document(session['student_department']).collection('semester').document(session['student_semester'])
            div_details = div_ref.get().to_dict()
            student_details = div_ref.collection('student').document(session['user']).get()
            attendance = {}
            if 'teacher_email' in div_details:
                final_subject=[]
                # get subject data
                for teacher_email in div_details['teacher_email']:
                    teacher_ref = db.collection('teacher').document(teacher_email)
                    actual_lec=db.collection('teacher').document(teacher_email).collection('department').document(session['student_department']).collection('semester').document(session['student_semester']).collection('subject').stream()
                    stored=db.collection('teacher').document(teacher_email).collection('department').document(session['student_department']).collection('semester').document(session['student_semester']).collection('subject')
                    for subjects in actual_lec:
                        subject=subjects.id
                        final_subject.append(subject)
                        lec_ref = stored.document(subject).collection('lecture')
                        teacher_details = teacher_ref.get().to_dict()
                        lectures = lec_ref.stream()
                        # conducted lec count & attendance calculation logic
                        lec_conducted_count = 0
                        lec_attended_count = 0
                        for lecture in lectures:
                            lec_conducted_count += 1
                            lec_dict = lecture.to_dict()
                            if session['user'] in lec_dict['student_email']:
                                lec_attended_count += 1
                            lectures = lec_ref.stream() # needs to be streamed again after every use, reason unkonwn
                        
                        if lec_conducted_count != 0:
                            percentage = int((lec_attended_count/lec_conducted_count)*100)
                        else:
                            percentage = 0
                        
                        attendance[subject] = [subject, teacher_details['name'], lec_attended_count, lec_conducted_count, percentage]
                        lectures = lec_ref.stream() # needs to be streamed again after every use, reason unkonwn
            
            div_details = div_ref.get().to_dict() # needs to be streamed again after every use, reason unkonwn
            return render_template('student_dashboard_page.html', final_subject=final_subject, student_details = student_details.to_dict(), div_details = div_details, division = session['student_department'], attendance = attendance, semester=session['student_semester'])
        if request.method=='POST':
            sub_details = request.form['sub_details']
            session['sub_details']=sub_details
            return redirect('/check_dates')

    else:
        return redirect('/logout')


@app.route('/check_dates', methods=['GET'])
def check_dates():    
    if 'user' in session and session['person_type'] == 'student':
        div_ref = db.collection('department').document(session['student_department']).collection('semester').document(session['student_semester'])
        student_details = div_ref.collection('student').document(session['user']).get()
        sub_details=session['sub_details']
        
        # student_attended_bool=[]
        subject_dates=[]
        subject_attendance={}
        teachers=db.collection('teacher').stream()
        for teacher in teachers:
            new_teacher=teacher.id
            check_department=db.collection('teacher').document(new_teacher).collection('department').stream()
            for department in check_department:
                if department.id == session['student_department']:
                    check_semester=db.collection('teacher').document(new_teacher).collection('department').document(session['student_department']).collection('semester').stream()
                    for semester in check_semester:
                        if semester.id ==session['student_semester']:
                            check_subject=db.collection('teacher').document(new_teacher).collection('department').document(session['student_department']).collection('semester').document(session['student_semester']).collection('subject').stream()
                            for subject in check_subject:
                                if subject.id == sub_details:
                                    lectures=db.collection('teacher').document(new_teacher).collection('department').document(session['student_department']).collection('semester').document(session['student_semester']).collection('subject').document(session['sub_details']).collection('lecture').stream()
                                    for lecture in lectures:
                                        lec_dict=lecture.to_dict()
                                        subject_dates.append(lec_dict['date'])
                                        if session['user'] in lec_dict['student_email']:
                                            student_attended_bool=True
                                            subject_attendance[lec_dict['date']] = [lec_dict['date'],  student_attended_bool]
                                        else:
                                            student_attended_bool=False
                                            subject_attendance[lec_dict['date']] = [lec_dict['date'],  student_attended_bool]
                                        
        print(subject_attendance)
        return render_template('check_dates.html',subject_dates=subject_dates, sub_details=sub_details, student_details = student_details.to_dict(), subject_attendance=subject_attendance )
    else:
        return redirect('/student_dashboard')











@app.route('/logout', methods = ['GET'])
def logout():
    if 'user' in session:
        session.pop('user', None)
        session.pop('person_type', None)
        session.pop('division', None)

        flash('You have been logged out...', 'warning')
        return redirect('/')
    else:
        return redirect('/')



@app.route('/forgot_password', methods = ['GET', 'POST'])
def forgotPassword():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('forgot_password_page.html')
        else:
            return redirect('/logout')
    elif request.method == 'POST':
        email = request.form['email']
        try:
            auth.send_password_reset_email(email)
        except:
            flash('That e-mail ID is not registered...', 'error')
            return redirect('/')
        flash('Check your e-mail to set new password...', 'info')
        return redirect('/')




if __name__ == '__main__':
    app.run(debug = False)