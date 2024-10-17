#Importing Flask and MySQL Libraries

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy 
from flask_wtf import FlaskForm 
from wtforms import StringField, FloatField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required

app = Flask(__name__) 

# Logins the User
login = LoginManager(app)

# Retrieves the ID of the User from the Session
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# Configuration for Connecting to the MySQL Database

app.config['SECRET_KEY'] = 'your_secret_key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/stock1' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)

###### MySQL Tables ######

# Defining the User Table
class User(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True) 
    first_name = db.Column(db.String(80), nullable=False) 
    last_name = db.Column(db.String(100), nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=True)
    admin = db.Column(db.Boolean, default=False)
    
# Defining the Stock Table
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(30), unique=True, nullable=False)
    ticker_symbol = db.Column(db.String(4), unique=True, nullable=False)
    starting_market_price = db.Column(db.Float(10,2), nullable=False)
    current_market_price = db.Column(db.Float(10,2), nullable=False)
    number_of_total_shares = db.Column(db.Integer, nullable=False)
    number_of_shares_to_purchase = db.Column(db.Integer, nullable=False)

# Creates All Tables in the MySQL Server
with app.app_context(): db.create_all()

###### Flask Forms ######

# Form for Creating a User
class UserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm'), Length(min=8)])
    confirm = PasswordField()
    submit = SubmitField('Submit')

# Form for Logging in a User
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Form for Creating a Stock
class StockForm(FlaskForm):
    stock_name = StringField('Stock Name', validators=[DataRequired()])
    ticker_symbol = StringField('Ticker Symbol', validators=[DataRequired(),Length(max=4)])
    starting_market_price = FloatField('Starting Price', validators=[DataRequired()])
    number_of_total_shares = IntegerField('Number of Shares', validators=[DataRequired()])
    submit = SubmitField('Submit')

###### Routes ######

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home', username=username))
    return render_template('login.html')

@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    form = UserForm()
    if form.validate_on_submit():
        new_user = User( first_name=form.first_name.data, 
                        last_name=form.last_name.data, 
                        email=form.email.data, 
                        username=form.username.data, 
                        password=form.password.data )
        db.session.add(new_user)
        db.session.commit()
        flash("Account Created Successfully")
        return redirect(url_for('login'))
    return render_template('createaccount.html', form=form)

@app.route('/accountcanceled')
def accountcanceled():
    return render_template('accountcanceled.html')

@app.route('/home/<username>')
def home(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('home.html', username=user_information)

@app.route('/trade')
def trade():
    stocks = Stock.query.all()
    return render_template('trade.html', stocks=stocks)

@app.route('/stockviewer')
def stockviewer():
    return render_template('stockviewer.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portoflio.html')

@app.route('/transactionhistory')
def transactionhistory():
    return render_template('transactionhistory.html')

@app.route('/accounttransfer')
def accounttransfer():
    return render_template('accounttransfer.html')

@app.route('/adminstocks', methods=['GET', 'POST'])
def adminstocks():
    stocks = Stock.query.all()
    createform = StockForm()
    if createform.validate_on_submit():
        new_stock = Stock ( stock_name=createform.stock_name.data, 
                            ticker_symbol=createform.ticker_symbol.data, 
                            starting_market_price=createform.starting_market_price.data, 
                            current_market_price=createform.starting_market_price.data, 
                            number_of_total_shares=createform.number_of_total_shares.data,
                            number_of_shares_to_purchase=createform.number_of_total_shares.data 
                            )
        db.session.add(new_stock)
        db.session.commit()
        flash("Stock Created Successfully")
        return redirect(url_for('adminstocks'))
    return render_template('adminstocks.html', createform=createform, stocks=stocks)

@app.route('/adminmarkethours')
def adminsmarkethours():
    return render_template('adminmarkethours.html')

if __name__ == "__main__": app.run(debug=True)