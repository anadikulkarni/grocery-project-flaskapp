from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime
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
    print("##"*10 + "found user")
    return User.query.get(int(user_id))

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(100), unique = True, nullable = False)
    products = db.relationship("Product", backref="category", lazy=True, cascade = "all, delete")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    productName = db.Column(db.String(100), nullable = False)
    unit = db.Column(db.String(100), nullable = False)
    rateUnit = db.Column(db.Float, nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    categoryid = db.Column(db.Integer, db.ForeignKey("category.id"), nullable = False)
    cartitem = db.relationship("CartItem", backref="product", lazy=True)

class Manager(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable = False)
    productid = db.Column(db.Integer, db.ForeignKey("product.id"), nullable = False)
    productName = db.Column(db.String(100), nullable = False)
    unit = db.Column(db.String(100), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    rateUnit = db.Column(db.Float, nullable = False)
    category = db.Column(db.String(100), nullable = False)
    
class Ledger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable = False)
    productid = db.Column(db.Integer, db.ForeignKey("product.id"), nullable = False)
    productName = db.Column(db.String(100), nullable = False)
    unit = db.Column(db.String(100), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    rateUnit = db.Column(db.Float, nullable = False)
    category = db.Column(db.String(100), nullable = False)
    purchaseDate = db.Column(db.DateTime, default = datetime.utcnow)
    
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
            
        return redirect(url_for("home"))
    return render_template('register.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    if (current_user.is_authenticated) and (current_user.username not in manager_creds):
        return redirect(url_for('user_dashboard'))
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if (user and user.password == form.password.data) and (form.username.data not in manager_creds):
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            error = "invalid username or password"
    return render_template('login.html', form=form, error=error)

@app.route('/manager_login', methods=["GET", "POST"])
def manager_login():
    if (current_user.is_authenticated) and (current_user.username in manager_creds):
        return redirect(url_for('categories'))
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if (user and user.password == form.password.data) and (form.username.data in manager_creds):
            login_user(user)
            return redirect(url_for('categories'))
        else:
            error = "invalid username or password"
    return render_template('manager_login.html', form=form, error=error)
 
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
    if (current_user.is_authenticated) and (current_user.username in manager_creds):
        categories = Category.query.all()
        return render_template('categories.html', categories=categories, manager=current_user)
    else:
        return redirect(url_for('home'))

@app.route('/save_category', methods=['POST'])
def save_category():
    data = request.json
    categoryName = data.get("categoryName")
    if not categoryName:
        return jsonify({'status': 'error',
                        'message': 'category name is required'}), 400
    new_category = Category(name=categoryName)
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'category saved successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/save_product', methods=['POST'])
def save_product():
    data = request.json
    categoryid = data.get("categoryid")
    productName = data.get("productName")
    unit = data.get("unit")
    rateUnit = data.get("rateUnit")
    quantity = data.get("quantity")
    category = Category.query.get(categoryid)
    if not productName:
        return jsonify({'status': 'error',
                        'message': 'product name is required'}), 400
    new_product = Product(category=category, productName=productName, unit=unit, rateUnit=rateUnit, quantity=quantity)
    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'product saved successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/products')
def products():
    products = Product.query.all()
    category = Category.query.first()
    print(category)
    productOfCategory = category.products
    print(productOfCategory)
    return render_template('products.html', products=products)

@app.route('/update_category', methods=['POST'])
def update_category():
    data = request.json
    categoryID = data.get("categoryID")
    categoryName = data.get("categoryName")
    try:
        category = Category.query.get(categoryID)
        if not category:
            return jsonify({'message': 'category not found'}), 404
        category.name = categoryName
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'category saved successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/delete_category', methods=['POST'])
def delete_category():
    data = request.json
    categoryID = data.get("categoryID")
    try:
        category = Category.query.get(categoryID)
        if not category:
            return jsonify({'message': 'category not found'}), 404
        db.session.delete(category)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'category deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.json
    productID = data.get("productID")
    productName = data.get("productName")
    unit = data.get("unit")
    rateUnit = data.get("rateUnit")
    quantity = data.get("quantity")
    product = Product.query.get(productID)
    if not product:
        return jsonify({'status': 'error',
                        'message': 'product not found'}), 404
    product.productName = productName
    product.unit = unit
    product.rateUnit = rateUnit
    product.quantity = quantity
    try:
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'product edited successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/delete_product', methods=['POST'])
def delete_product():
    data = request.json
    productID = data.get("productID")
    try:
        product = Product.query.get(productID)
        if not product:
            return jsonify({'message': 'product not found'}), 404
        db.session.delete(product)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':'product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/user_dashboard')
def user_dashboard():
    if (current_user.is_authenticated) and (current_user.username not in manager_creds):
        categories = Category.query.all()
        products = Product.query.all()
        return render_template('user_dashboard.html', categories=categories, products=products, user=current_user)
    else:
        return redirect(url_for('home'))

@app.route('/purchase_product', methods=['POST'])
def purchase_product():
    data = request.json
    productID = data.get("productID")
    quantity = int(data.get("quantity"))
    userID = data.get("userID")
    try:
        product = Product.query.get(productID)
        productName = product.productName
        unit = product.unit
        rateUnit = product.rateUnit
        category = product.category.name
        ledger = Ledger(userid=userID, productName=productName, productid=productID, unit=unit,
                            quantity=quantity, rateUnit=rateUnit, category = category)
        if not product:
            return jsonify({'message': 'product not found'}), 404
        if product.quantity < quantity:
            return jsonify({'status':'success',
                'message':f'not enough stock, remaining quantity: {product.quantity}'})

        product.quantity -= quantity
        db.session.add(ledger)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':f'product purchased successfully, remaining quantity: {product.quantity}'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/cart')
def cart():
    items = CartItem.query.filter_by(userid = current_user.id).all()
    return render_template('cart.html', items = items, user=current_user)

@app.route('/add_to_cart_product', methods=['POST'])
def add_to_cart_product():
    data = request.json
    productID = data.get("productID")
    quantity = int(data.get("quantity"))
    userID = data.get("userID")
    try:
        product = Product.query.get(productID)
        productName = product.productName
        unit = product.unit
        rateUnit = product.rateUnit
        category = product.category.name
        cartitem = CartItem(userid=userID, productName=productName, productid=productID, unit=unit,
                            quantity=quantity, rateUnit=rateUnit, category = category)
        if not product:
            return jsonify({'message': 'product not found'}), 404
        if product.quantity < quantity:
            return jsonify({'status':'success',
                'message':f'not enough stock, remaining quantity: {product.quantity}'})

        product.quantity -= quantity
        db.session.add(cartitem)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':f'product added to cart successfully, remaining quantity: {product.quantity}'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/buy_all', methods = ['POST'])
def buy_all():
    data = request.json
    print(data)
    try:
        cart_items = CartItem.query.filter_by(userid = current_user.id).all()
        for item in cart_items:
            ledger = Ledger(userid=item.userid, productName=item.productName, productid=item.productid, unit=item.unit,
                            quantity=item.quantity, rateUnit=item.rateUnit, category = item.category)
            db.session.add(ledger)
            db.session.delete(item)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':f'products bought successfully'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500
        
@app.route('/remove_item', methods=['POST'])
def remove_item():
    data = request.json
    itemid = data.get("itemid")
    try:
        cartitem = CartItem.query.get(itemid)
        quantity = cartitem.quantity
        productid = cartitem.productid
        product = Product.query.get(productid)
        if not product:
            return jsonify({'message': 'product not found'}), 404
        if product.quantity < quantity:
            return jsonify({'status':'success',
                'message':f'not enough stock, remaining quantity: {product.quantity}'})

        product.quantity += quantity
        db.session.delete(cartitem)
        db.session.commit()
        return jsonify({'status':'success',
                        'message':f'product removed from cart successfully, remaining quantity: {product.quantity}'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status':'error',
                        'message':f'an error occurred: {str(e)}'}), 500

@app.route('/summary')
def summary():
    manager = current_user
    return render_template('summary.html', manager=manager)

@app.route('/data/purchases_per_category')
def purchases_per_category():
    results = db.session.query(Ledger.category, db.func.count(Ledger.id)).group_by(Ledger.category).all()
    data = [[category, count] for category, count in results]
    return jsonify(data) 

@app.route('/data/earnings_per_category')
def earnings_per_category():
    results = db.session.query(Ledger.category, db.func.sum(Ledger.rateUnit * Ledger.quantity)).group_by(Ledger.category).all()
    data = [[category, earning] for category, earning in results]  
    return jsonify(data)

@app.route('/data/top_selling_products')
def top_selling_products():
    results = db.session.query(Ledger.productName, db.func.sum(Ledger.quantity)).group_by(Ledger.productName).order_by(db.func.sum(Ledger.quantity).desc()).limit(5).all()
    data = [[productName, count] for productName, count in results]  
    return jsonify(data)
  
if __name__ == "__main__":
    app.run(debug=True)
    


