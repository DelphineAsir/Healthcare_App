
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from werkzeug.utils import secure_filename
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np
from datetime import datetime

UPLOAD_FOLDER=""
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.secret_key = '5'

app.config['MYSQL_HOST'] = 'parkinson.cpiy0qi2g80z.ap-southeast-2.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'parkinson'

mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = % s AND password = % s', (username, password, ))
		account = cursor.fetchone()
		if account:
			session['loggedin'] = True
			session['id'] = account['id']
			session['username'] = account['username']
			msg = 'Logged in successfully !'
			return render_template('index.html', msg = msg)
		else:
			msg = 'Incorrect username / password !'
	return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = % s', (username, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		elif not username or not password or not email:
			msg = 'Please fill out the form !'
		else:
			cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (username, password, email, ))
			cursor.execute('CREATE TABLE IF NOT EXISTS `%s` (pid int(11) NOT NULL AUTO_INCREMENT, pname varchar(50) NOT NULL, age varchar(50) NOT NULL, gender varchar(100) NOT NULL,pdate date NOT NULL, pstatus varchar(100) NOT NULL, PRIMARY KEY(pid)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;' % (username,))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('register.html', msg = msg)


model_s = load_model('model/spiral_model.h5')
model_w = load_model('model/wave_model.h5')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(file_storage):
    # Save the uploaded file to a temporary location
    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(file_path)
    
    # Load the image 
    img_array = image.load_img(file_path, target_size=(224, 224))
    img_array = image.img_to_array(img_array)
    img_array = np.expand_dims(img_array, axis=0)  
    img_array /= 255.0 
    print(img_array.shape)
    return img_array

def predict_parkinsons(img_s):
    prediction_s = model_s.predict(img_s)
    class_indices = {0: 'healthy', 1: 'parkinson'}
    predicted_class_index = np.argmax(prediction_s)
    prediction = class_indices[predicted_class_index]
    return prediction

def SAVE_DATA(name,age,gender,prediction):
	try:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		prediction_time = datetime.now()
		query = "INSERT INTO `{}` VALUES (NULL, %s, %s, %s, %s, %s)".format(session.get('username'))    
		cursor.execute(query, (name, age, gender, prediction_time, prediction))
		mysql.connection.commit()
	except Exception as e:
		mysql.connection.rollback()
		print("Error occurred while storing prediction data:", e)
	finally:
		cursor.close()

@app.route('/predict', methods =['GET', 'POST'])
def predict():
	if 'username' not in session:
		return redirect(url_for('login'))

	name = request.form['name']
	age = request.form['age']
	gender = request.form['gender']
	img_spiral = request.files['spiral_image']

	if img_spiral and allowed_file(img_spiral.filename):
		img_spiral_processed = preprocess_image(img_spiral)
		prediction = predict_parkinsons(img_spiral_processed)
		SAVE_DATA(name,age,gender,prediction)
		return render_template('index.html', prediction=prediction)
	else:
		return jsonify({'error': 'Invalid file format'})
	

@app.route('/form1', methods =['GET', 'POST'])
def form1():
	return render_template('form1.html')

def predict_parkinsons_w(img_w):
    prediction_w = model_w.predict(img_w)
    class_indices = {0: 'healthy', 1: 'parkinson'}
    predicted_class_index = np.argmax(prediction_w)
    prediction = class_indices[predicted_class_index]
    return prediction

@app.route('/predict2', methods =['GET', 'POST'])
def predict2():
	if 'username' not in session:
		return redirect(url_for('login'))

	name = request.form['name']
	age = request.form['age']
	gender = request.form['gender']
	img_wave = request.files['wave_image']

	if img_wave and allowed_file(img_wave.filename):
		img_wave_processed = preprocess_image(img_wave)
		prediction = predict_parkinsons_w(img_wave_processed)
		SAVE_DATA(name,age,gender,prediction)
		return render_template('index.html', prediction=prediction)
	else:
		return jsonify({'error': 'Invalid file format'})

@app.route('/form2')
def form2():
    return render_template('form2.html')	

@app.route('/index')
def index():
    return render_template('index.html')	

def get_patient_details():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM `%s`" % session.get('username'))
        patient_details = cursor.fetchall()
        return patient_details
    except Exception as e:
        print("Error occurred while fetching patient details:", e)
        return None
    finally:
        cursor.close()

@app.route('/view')
def view():
	if 'username' not in session:
		return redirect(url_for('login'))
	patient_details = get_patient_details()

	if patient_details:
		return render_template('patient.html', patient_details=patient_details)
	else:
		return "Failed to fetch patient details from the database."

if __name__ == '__main__':
    app.run(debug=True)
