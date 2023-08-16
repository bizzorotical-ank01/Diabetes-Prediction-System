from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from models import db, UserModel
from flask_bcrypt import Bcrypt
import pandas as pd
import secrets
import joblib


app = Flask(__name__)
bcrypt = Bcrypt(app)
db.init_app(app)
app.secret_key = secrets.token_bytes(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/')
def hello():
    return render_template('index.html', logged_in=current_user.is_authenticated)


@app.route('/analysis')
def analysis():
    return render_template('analysis.html', logged_in=current_user.is_authenticated)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        form_data = dict(request.form)
        user = UserModel.query.filter_by(email=form_data['email']).first()
        if user:
            if bcrypt.check_password_hash(user.password, form_data['password']):
                login_user(user)
                return render_template('user_demographics.html')
            else:
                return {
                    "message": "Incorrect Password for {}".format(form_data['email']),
                    "status": 404
                }
        else:
            return {
                "message": "User {} doesn't exist. Please register on the register page".format(form_data['email']),
                "status": 404
            }
    elif request.method == "GET":
        return render_template('login.html')
    else:
        return {
            "message": 'Method not allowed, only GET and POST methods are entertained',
            "status": 404
        }


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        form_data = dict(request.form)
        data = {
            'username': form_data['name'],
            'email': form_data['email'],
            'password': bcrypt.generate_password_hash(form_data['password'])
        }

        new_user = UserModel(data)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    elif request.method == "GET":
        return render_template('register.html')

    else:
        return {
            "message": 'Method not allowed, only GET and POST methods are entertained',
            "status": 404
        }

### give your training file

@app.route('/clean_data', methods=["POST"])
def clean_data():

    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            csv_data = ''

            with open('./data.csv', 'w') as data_file:
                for row in data:
                    csv_data += ",".join(row.values()) + '\n'

                data_file.write(csv_data)
# read file
            Diabetee = pd.read_csv('./data.csv', names=data[0].keys())

            min_max = MinMaxScaler()
            columns_to_scale = ['Age', 'BP', 'BMI', 'Glucose','Outcome'] ##BMI is Body Mass Index
            Diabetee[columns_to_scale] = min_max.fit_transform(
                Diabetee[columns_to_scale])
# dividing into traing and testing files on the basis of test file size given by user
            x = Diabetee[['Age', 'BP', 'BMI', 'Glucose','Outcome']]
            y = Diabetee['Diabetes']
            x_train, x_test, y_train, y_test = train_test_split(
                x, y, test_size=0.30)
# Make records
            data = {
                'headers': ['Age', 'BP', 'BMI', 'Glucose'],
                'clean_data': (x.join(y)).to_dict('records'),
                'train_data': (x_train.join(y_train)).to_dict('records'),
                'test_data': (x_test.join(y_test)).to_dict('records')
            }

            return {'message': 'Success', 'data': data, 'status': 200}
        except Exception as error:
            return {'message': 'Failed - Internal Server Error - {}'.format(error), 'status': 500}
    else:
        return {'message': 'Method not allowed, only POST method is supported', 'status': 404}

#Running training and testing files
@app.route('/train_model', methods=["POST"])
def train_model():

    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            train_data = pd.DataFrame(data['train_data'])
            test_data = pd.DataFrame(data['test_data'])
            x_train, y_train = train_data[[
                'Age', 'BP', 'BMI', 'Glucose']], train_data['Diabetes']
            x_test, y_test = test_data[[
                'Age', 'BP', 'BMI', 'Glucose']], test_data['Diabetes']
#applying Algo
            model = LogisticRegression()
            model.fit(x_train, y_train)
            y_pred = model.predict(x_test)

            joblib.dump(model, "model.pkl")

            return {
                'message': 'Logistic Regression, Training Successfull',
                'body': 'Accuracy Score for Trained LR Model : {}'.format(accuracy_score(y_test, y_pred)*100),
                'status': 200
            }

        except Exception as error:
            return {'message': 'Failed - Internal Server Error - {}'.format(error), 'status': 500}
    else:
        return {'message': 'Method not allowed, only POST method is supported', 'status': 404}

#Data entered at run time for predictions
@app.route('/user_demographics', methods=['GET', 'POST'])
@login_required
def user_demographics():
    if request.method == "GET":
        return render_template('user_demographics.html')
    elif request.method == "POST":
        try:
            # Get data from form and make predictions
            user_data = dict(request.get_json())['values']
            print(user_data)
            loaded_model = joblib.load('model.pkl')
            prediction = loaded_model.predict(user_data)
            print(prediction)

            return {
                "message": "PREDICTION BASED ON USER DATA", 
                'body': 'The algorithm infered {} of Diabetes'.format(prediction[0]), 
                "status": 200
            }
        except Exception as error:
            return {'message': 'Failed - Internal Server Error - {}'.format(error), 'status': 500}
    else:
        return {'message': 'Method not allowed, only POST method is supported', 'status': 404}

#db server over your web browser
if __name__ == "__main__":
    app.run('localhost', 8080, debug=True, use_reloader=True)


