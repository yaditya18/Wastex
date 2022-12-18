# from __future__ import division
from flask import Flask, render_template, url_for, request, redirect, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import storage
import pyrebase
import main
import urllib.request
from werkzeug.utils import secure_filename
from main import getPrediction
import os

UPLOAD_FOLDER = '/mnt/c/Users/Aditya/Desktop/Aditya-Project/static/'               
app = Flask(__name__)

app.secret_key = '2' # for flask session

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Use a service account
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# pyrebase init
# Your web app's Firebase configuration
firebaseConfig = {
  'apiKey': "AIzaSyCjjMT0-WW7KMmftyrcF2zX44SHN4soFVw",
  'authDomain': "wastex-63243.firebaseapp.com",
  'databaseURL': "https://wastex-63243-default-rtdb.asia-southeast1.firebasedatabase.app",
  'projectId': "wastex-63243",
  'storageBucket': "wastex-63243.appspot.com",
  'messagingSenderId': "484238868185",
  'appId': "1:484238868185:web:ef74f8844ad4d6ea8908c8",
  'measurementId': "G-92JYD5VK35",
  'serviceAccount': "key.json"
}

firebase = pyrebase.initialize_app(firebaseConfig)
storage=firebase.storage()

auth = firebase.auth()


@app.route('/', methods = ['GET'])
def home_page():
    if 'user' not in session:
        return render_template('home_page.html')
    else:
        return redirect('/logout')



@app.route('/seller_login', methods = ['GET', 'POST'])
def seller_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('seller_login_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        flag_1=flag_2=False
        seller_emails=db.collection('seller').stream()
        for seller_email in seller_emails:
            if seller_email.id == email:
                flag_1=True
                # check Password 
                try:
                    seller_user=auth.sign_in_with_email_and_password(email, password)
                    flag_2=True
                except:
                    flag_2=False
                break
        # check the flags
        if flag_1==False or flag_2==False:
            flash('Incorrect, unverified or non-existent e-mail, division or password...', 'error')
            return redirect('/seller_login')

        session['user']=email
        session['person_type']='seller'
        # return redirect('/seller_dashboard')
        return redirect('/seller_home')







@app.route('/seller_signup', methods = ['GET', 'POST'])
def seller_signup():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('seller_signup_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        phone=request.form['phone']
        address=request.form['address']

        # check if passwords match
        if password != password2:
            flash('The passwords do not match...', 'error')
            return redirect('/seller_signup')
        # check length of pass
        if len(password) < 6:
            flash('The password has to be more than 5 characters long...', 'error')
            return redirect('/seller_signup')
        
        # auth user
        try:
            seller_user = auth.create_user_with_email_and_password(email, password)
        except:
            flash('This e-mail has already been registered. Please use another e-mail...', 'error')
            return redirect('/seller_signup')
        # e-mail verification
        # auth.send_email_verification(seller_user['idToken'])
        # add seller to db
        db.collection('seller').document(email).set({
            'name': name,
            'email': email,
            'phone':phone,
            'address':address,
            'password': password # firebase auth
        })

        flash('Registration successful! Please check your e-mail for verification and then log in...', 'info')
        return redirect('/seller_login')





@app.route("/seller_home", methods = ['GET', 'POST']) #/file
# Our function for pushing the image to the classifier model
def seller_home():
    if 'user' in session and session['person_type']=='seller':
        if request.method=='GET':
            return render_template('seller_home_page.html')

        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return render_template('seller_home_page.html')
            file = request.files['file']
            # Error message if no file submitted
            if file.filename == '':
                flash('No file selected for uploading')
                return render_template('seller_home_page.html')
            # Return results predictive data
            if file:
                global filename
                filename=secure_filename(file.filename)
                global directory
                directory = file.save(os.path.join('/mnt/c/Users/Aditya/Desktop/Aditya-Project/static/', filename))
                global pre
                pre = getPrediction(filename)
                print(getPrediction(filename))
                # answer, probability_results, filename = getPrediction(filename)
                # flash(answer)
                # flash(probability_results) # accuracy
                # flash(filename)
                # return render_template('uploaded_file.html')
                return redirect('/add_file')




@app.route('/add_file', methods=['GET', 'POST'])
def add_file():
    if 'user' in session and session['person_type']=='seller':
        if request.method=='GET':
            answer, probability_results, filename = pre
            session['filename']=filename
            flash(answer)
            flash(probability_results) # accuracy
            flash(filename)
            print(directory)
            return render_template('add_file.html')

        if request.method=='POST':
            path=os.path.join('/mnt/c/Users/Aditya/Desktop/Aditya-Project/static/', session['filename'])
            storage.child(session['filename']).put(path)
            flash('The Image has ben added to the firebase storage')
            return redirect('/seller_home')




# @app.route('/seller_add_item', methods=['POST'])
# def seller_add_items():
#     if 'user' in session and session['person_type']=='seller':
#         if request.method=='POST':
#             # print(filename)
#             path=os.path.join('/mnt/c/Users/colle/OneDrive/Desktop/Aditya-Project/static/', filename)
#             storage.child(filename).put(path)
#             flash('The Image has ben added to the firebase storage')
#             return render_template('seller_home_page.html')










@app.route('/buyer_login', methods = ['GET', 'POST'])
def buyer_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('buyer_login_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # check e-mail, div & pass
        flag_2 = flag_3 = False
        buyers = db.collection('buyer')
        divs = buyers.stream()
        # check for div existence
        # for div in divs:
        #     if div.id == department:
        #         flag_1 = True
        #         div_buyer_details = div_ref.document(department).collection('semester').document(sem).collection('buyer').stream()
        #         # check for buyer existence in div
        for buyer in divs:
            if buyer.id == email:
                flag_2 = True
        #                 # check pass
        try:
            st_user = auth.sign_in_with_email_and_password(email, password)
            flag_3 = True
#                     # e-mail verification check
#                     # acc_info = auth.get_account_info(st_user['idToken'])
#                     # if acc_info['users'][0]['emailVerified'] == True:
#                     flag_4 = True
        except:
            flag_3 = False
        #                 break
        #         break

        if flag_3==False or flag_2==False:
            flash('Incorrect, unverified or non-existent e-mail, department or password...', 'error')
            return redirect('/buyer_login')

        # session['buyer_department'] = department
        # session['buyer_semester']=sem
        session['user'] = email
        session['person_type'] = 'buyer'
        # return redirect('/buyer_dashboard')
        # return redirect('/buyer_dashboard')
        return render_template('success.html')


@app.route('/buyer_signup', methods = ['GET', 'POST'])
def buyer_signup():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('buyer_signup_page.html')
        else:
            return redirect('/logout')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        phone=request.form['phone']
        address=request.form['address']

        # check if passwords match
        if password != password2:
            flash('The passwords do not match...', 'error')
            return redirect('/buyer_signup')
        # check length of pass
        if len(password) < 6:
            flash('The password has to be more than 5 characters long...', 'error')
            return redirect('/buyer_signup')
        
        # auth user
        try:
            buyer_user = auth.create_user_with_email_and_password(email, password)
        except:
            flash('This e-mail has already been registered. Please use another e-mail...', 'error')
            return redirect('/buyer_signup')
        # e-mail verification
        # auth.send_email_verification(seller_user['idToken'])
        # add seller to db
        db.collection('buyer').document(email).set({
            'name': name,
            'email': email,
            'phone':phone,
            'address':address,
            'password': password # firebase auth
        })

        flash('Registration successful! Please check your e-mail for verification and then log in...', 'info')
        return redirect('/buyer_login')


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

if __name__ == '__main__':
    app.run(debug = True)