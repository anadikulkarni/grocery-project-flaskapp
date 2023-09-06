from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.exc import IntegrityError
import json

manager_creds = {'admin' : 'password',
                 'manager2' : 'managerpass'}

with open("config.json") as config:
    configdata = json.load(config)
    
app = Flask(__name__)
app.config['SECRET_KEY'] = configdata['SECRETKEY']
app.config["SQLALCHEMY_DATABASE_URI"] = configdata["SQLALCHEMY_DATABASE_URI"]

loginmanager = LoginManager()
loginmanager.init_app(app)

@loginmanager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(100), unique = True, nullable = False)
    def __init__(self, name):
        self.name = name

class Manager(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")
    
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    
with app.app_context():
   db.create_all()

@app.route('/user')
def show_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/category_list')
def show_categories():
    categories = Category.query.all()
    return render_template('category_list.html', categories=categories)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            new_user = User(username = form.username.data, 
                        password = form.password.data)
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            
        return redirect(url_for("show_users"))
    return render_template('register.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return render_template('homepage.html')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return render_template('homepage.html')
        else:
            return "invalid username or password"
    return render_template('login.html', form=form)

@app.route('/manager_login', methods=["GET", "POST"])
def manager_login():
    if current_user.is_authenticated:
        return render_template('categories.html')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return render_template('categories.html')
        else:
            return "invalid username or password"
    return render_template('manager_login.html', form=form)
 
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/save_category', methods=['POST'])
def save_category():
    data = request.json
    categoryName = data.get("categoryName")
    if not categoryName:
        return jsonify({'status': 'error',
                        'message': 'category name is required'})
    new_category = Category(name=categoryName)
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'category saved successfully'})
    except Exception as e:
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'})
  
if __name__ == "__main__":
    app.run(debug=True)
    


