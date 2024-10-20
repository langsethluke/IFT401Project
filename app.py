#Importing Flask and MySQL Libraries

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_wtf import FlaskForm 
from wtforms import StringField, FloatField, IntegerField, SubmitField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required
from decimal import Decimal
from sqlalchemy.ext.hybrid import hybrid_property

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
app.config['WTF_CSRF_ENABLED'] = False

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

    # Creating the relationship with the Portfolio Table
    portfolio = db.relationship('Portfolio', back_populates='user', uselist=False)

# Defining the Portfolio Table
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_balance = db.Column(db.Float(20,2), nullable=False)
    stock_balance = db.Column(db.Float(20,2), nullable=False)
    cash_balance = db.Column(db.Float(20,2), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    # Creating the relationship with the User Table
    user = db.relationship('User', back_populates='portfolio')

    # Creating the relationship with the Portfolio Transaction Table
    portfoliotransaction = db.relationship('PortfolioTransaction', back_populates='portfolio', uselist=True)

@event.listens_for(Portfolio, 'before_insert')
@event.listens_for(Portfolio, 'before_update')
def update_total_balance(mapper, connection, target):
        target.total_balance = target.stock_balance + target.cash_balance

# Defining the Portfolio Transaction Table
class PortfolioTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(8), nullable=False)
    amount = db.Column(db.Float(10,2), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)

    #Creating the relationship with the Portofolio Table
    portfolio = db.relationship('Portfolio', back_populates='portfoliotransaction')

# Defining the Stock Table
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(30), unique=True, nullable=False)
    ticker_symbol = db.Column(db.String(4), unique=True, nullable=False)
    starting_market_price = db.Column(db.Float(20,2), nullable=False)
    current_market_price = db.Column(db.Float(20,2), nullable=False)
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

# Form for Deposit
class DepositForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Deposit')

# Form for Withdraw
class WithdrawForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Withdraw')

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
    userForm = UserForm()
    if userForm.validate_on_submit():
        new_user = User( 
                        first_name=userForm.first_name.data, 
                        last_name=userForm.last_name.data, 
                        email=userForm.email.data, 
                        username=userForm.username.data, 
                        password=userForm.password.data )
        
        # Commits the User first so the Portfolio can get a valid User ID
        db.session.add(new_user)
        db.session.commit()
    
        new_portfolio = Portfolio(
                        total_balance = 0,
                        stock_balance = 0,
                        cash_balance = 0,
                        user_id = new_user.id )

        db.session.add(new_portfolio)
        db.session.commit()
        flash("Account Created Successfully")
        return redirect(url_for('login'))
    return render_template('createaccount.html', userForm=userForm)

@app.route('/accountcanceled')
def accountcanceled():
    return render_template('accountcanceled.html')

@app.route('/home/<username>')
def home(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    return render_template('home.html', user_information=user_information, portfolio=portfolio_information)

@app.route('/trade/<username>')
def trade(username):
    stocks = Stock.query.all()
    user_information = User.query.filter_by(username=username).first()
    return render_template('trade.html', user_information=user_information, stocks=stocks)

@app.route('/stockviewer/<stockname>/<username>')
def stockviewer(username, stockname):
    user_information = User.query.filter_by(username=username).first()
    stock_information = Stock.query.filter_by(stock_name=stockname).first()
    print(stock_information)
    return render_template('stockviewer.html', user_information=user_information, stock_information=stock_information)

@app.route('/portfolio/<username>')
def portfolio(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('portoflio.html',user_information=user_information)

@app.route('/tradehistory/<username>')
def tradehistory(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('tradehistory.html', user_information=user_information)

@app.route('/accounttransfer/<username>', methods=['GET', 'POST'])
def accounttransfer(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    portfolio_transactions =  PortfolioTransaction.query.all()

    depositForm = DepositForm(request.form)
    withdrawForm = WithdrawForm(request.form)

    if request.method == 'POST':
        if 'submit' in request.form:
            if request.form['submit'] == 'Deposit':
                amount = Decimal(depositForm.amount.data)
                if depositForm.validate_on_submit():
                    new_transaction = PortfolioTransaction (
                            type = "Deposit",
                            amount = amount,
                            portfolio_id = portfolio_information.id
                        )
                    portfolio_information.cash_balance += amount
                    db.session.add(new_transaction)
                    db.session.commit()
                    return redirect(url_for('accounttransfer', username=username)) 
            elif request.form['submit'] == 'Withdraw':
                amount = Decimal(depositForm.amount.data)
                if withdrawForm.validate_on_submit():
                    if amount < portfolio_information.cash_balance:
                        new_transaction = PortfolioTransaction (
                                type = "Withdraw",
                                amount = amount,
                                portfolio_id = portfolio_information.id
                            )
                        portfolio_information.cash_balance -= amount
                        db.session.add(new_transaction)
                        db.session.commit()
                        return redirect(url_for('accounttransfer', username=username))
                    else:
                        return redirect(url_for('accounttransfer', username=username))

    return render_template('accounttransfer.html', user_information=user_information, portfolio=portfolio_information, depositForm=depositForm, withdrawForm=withdrawForm,  portfolio_transactions= portfolio_transactions)

@app.route('/adminstocks/<username>', methods=['GET', 'POST'])
def adminstocks(username):
    user_information = User.query.filter_by(username=username).first()
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
        return redirect(url_for('adminstocks',  username=username))
    return render_template('adminstocks.html', user_information=user_information, createform=createform, stocks=stocks)

@app.route('/adminmarkethours/<username>')
def adminmarkethours(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('adminmarkethours.html', user_information=user_information)

if __name__ == "__main__": app.run(debug=True)