import pyrebase
from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin



firebaseConfig = {
    'apiKey': "AIzaSyCjjMT0-WW7KMmftyrcF2zX44SHN4soFVw",
    'authDomain': "wastex-63243.firebaseapp.com",
    'projectId': "wastex-63243",
    'storageBucket': "wastex-63243.appspot.com",
    'messagingSenderId': "484238868185",
    'appId': "1:484238868185:web:ef74f8844ad4d6ea8908c8",
    'measurementId': "G-92JYD5VK35"
  }

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

db=firestore.client()
db.collection('new').document('aditya').set({'name':'aditya'})