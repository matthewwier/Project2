from flask import Flask, render_template, request, json, session, redirect, url_for, send_from_directory
from flaskext.mysql import MySQL
from werkzeug.utils import secure_filename
import hashlib
import os

app = Flask(__name__)
app.secret_key = "key"
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'maciek'
app.config['MYSQL_DATABASE_DB'] = 'Users'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
mysql.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file',
                                filename=filename))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route("/")
def main():
    return render_template('index.html')


@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

@app.route('/showSignIn')
def showSignIn():
    return render_template('signin.html')

# implementuje zadanie request z flaska

@app.route('/signUp', methods=['GET','POST'])
def signUp():
    try:
        if request.method == 'GET':
            print 'tuget'
            return redirect('/')
        elif request.method == 'POST':
            print 'tupost'
            _name = request.form['inputName']
            _email = request.form['inputEmail']
            _password = request.form['inputPassword']

            # validate the received values
            if _name and _email and _password:

                conn = mysql.connect()
                cursor = conn.cursor()
                _hashed_password = hashlib.sha1(_password).hexdigest()
                cursor.callproc('sp_createUser', (_name, _email, _hashed_password, 2))
                cursor.callproc('sp_addRole', (_name, 2))
                data = cursor.fetchall()
                print data
                if len(data) is 0:
                    conn.commit()
                    #return json.dumps({'message': 'User created successfully !'})
                    return render_template('success.html')
                else:
                    #return json.dumps({'error': str(data[0])})
                    return render_template('error.html', error='Bad! This user exists!')
            else:
                print 'tucosinnego'
                return redirect('/')
                #return json.dumps({'html': '<span>Enter the required fields</span>'})
        else:
            return redirect('/')
            #return render_template('signup.html')

    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        cursor.close()
        conn.close()


@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        # connect to mysql
        print _username+" "
        print _password
        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()
        if len(data) > 0:
            if str(data[0][3]) == str(hashlib.sha1(_password).hexdigest())[:20]:
                print data
                session['user'] = data[0][0]
                print session['user']
                connect = mysql.connect()
                cursorr = connect.cursor()
                cursorr.callproc('sp_findUserByUserName', (_username,))
                dat = cursorr.fetchall()
                print dat
                conn = mysql.connect()
                curr = conn.cursor()
                curr.callproc('sp_findRole', (dat[0][0],))
                daat = curr.fetchall()
                role = daat[0][0]
                if role == 2:
                    # zwykly uzytkownik
                    return redirect('/userHome')
                else:
                    # jesli rola jest ADMIN
                    return render_template('adminHome.html')

            else:
                return render_template('error.html', error='Wrong Email address or Password.')
        else:
            return render_template('error.html', error='Wrong Email address or Password.')

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        cursor.close()
        con.close()


@app.route('/clearTasks', methods=['GET'])
def clearTasks():
    if session.get('user'):

        _user = session.get('user')

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.callproc('sp_deleteTasks', (_user,))
        data = cursor.fetchall()
        if len(data) is 0:
            conn.commit()
            return redirect('/userHome')
        else:
            return render_template('error.html', error="An arror occured")
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/showAddTask')
def showAddTask():
    return render_template('addTask.html')

@app.route('/showUploadFiles')
def showUploadFiles():
    return render_template('upload.html')

@app.route('/addTask', methods=['POST'])
def addTask():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish', (_title, _description, _user))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html', error="An arror occured")
        else:
            return render_template('error.html', error="Unauthorized Access")

    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        cursor.close()
        conn.close()






@app.route('/getTask')
def getTask():
    try:
        if session.get('user'):
            _user = session.get('user')

            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetWishByUser', (_user,))
            wishes = cursor.fetchall()

            wishes_dict = []
            for wish in wishes:
                wish_dict = {
                    'Id': wish[0],
                    'Title': wish[1],
                    'Description': wish[2],
                    'Date': wish[4]}
                wishes_dict.append(wish_dict)

            return json.dumps(wishes_dict)

        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run()



