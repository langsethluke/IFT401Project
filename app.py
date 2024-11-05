#Importing Flask and MySQL Libraries

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_wtf import FlaskForm 
from wtforms import StringField, FloatField, IntegerField, SubmitField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required
from decimal import Decimal
import time
import threading

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

    # Creating the relationship with the Portfolio Table
    stock_portfolio = db.relationship('StockPortfolio', back_populates='user', uselist=True)

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

# Changes the total_balance column based off when the stock and cash balance columns are changed
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
    opening_price = db.Column(db.Float, nullable=False)
    todays_high = db.Column(db.Float, nullable=False)
    todays_low = db.Column(db.Float, nullable=False)
    total_market_cap = db.Column(db.Float, nullable=False)

    # Creating the relationship with the StockPortfolio Table
    stock_portfolio = db.relationship('StockPortfolio', back_populates='stock', uselist=True)

    # Creating the relationship with the StockPriceHistoryDaily Table
    stock_price_history_daily = db.relationship('StockPriceHistoryDaily', back_populates='stock')

# Changes the total_market_cap column based off when the number_of_total_shares and current_market_price columns are changed
@event.listens_for(Stock, 'before_insert')
@event.listens_for(Stock, 'before_update')
def update_total_balance(mapper, connection, target):
        target.total_market_cap = target.current_market_price * target.number_of_total_shares

# Defining the Stock Pirce Daily History Table
class StockPriceHistoryDaily(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    nine_thirty = db.Column(db.Float)
    nine_fourty_five = db.Column(db.Float)
    ten = db.Column(db.Float)
    ten_fifteen = db.Column(db.Float)
    ten_thirty = db.Column(db.Float)
    ten_fourty_five = db.Column(db.Float)
    eleven = db.Column(db.Float)
    eleven_fifteen = db.Column(db.Float)
    eleven_thirty = db.Column(db.Float)
    eleven_fourty_five = db.Column(db.Float)
    twelve = db.Column(db.Float)
    twelve_fifteen = db.Column(db.Float)
    twelve_thirty = db.Column(db.Float)
    twelve_fourty_five = db.Column(db.Float)
    one = db.Column(db.Float)
    one_fifteen = db.Column(db.Float)
    one_thirty = db.Column(db.Float)
    one_fourty_five = db.Column(db.Float)
    two = db.Column(db.Float)
    two_fifteen = db.Column(db.Float)
    two_thirty = db.Column(db.Float)
    two_fourty_five = db.Column(db.Float)
    three = db.Column(db.Float)
    three_fifteen = db.Column(db.Float)
    three_thirty = db.Column(db.Float)
    three_fourty_five = db.Column(db.Float)
    four = db.Column(db.Float)
    four_fifteen = db.Column(db.Float)
    four_thirty = db.Column(db.Float)

    # Creating the relationship with the Stock Table
    stock = db.relationship('Stock', back_populates='stock_price_history_daily')


class StockPortfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(5), nullable=False)
    price_per_share = db.Column(db.Float(20,2), nullable=False)
    number_of_shares = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float(20,2), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Creating the relationship with the Stock Table
    stock = db.relationship('Stock', back_populates='stock_portfolio')

    # Creating the relationship with the User Table
    user = db.relationship('User', back_populates='stock_portfolio')

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

# Form for Buying and Selling a Stock
class TransactionStockForm(FlaskForm):
    numOfShares = IntegerField('Number of Shares', validators=[DataRequired()])
    submit = SubmitField('Buy')

##### Functions #####

# Calculates the Number of Shares Owned by a User for a Specific Stock
def calculate_shares_owned(user_id, stock_id):
    stock_portfolio_information = StockPortfolio.query.filter_by(user_id=user_id, stock_id=stock_id).all()

    numOfSharesOwned = 0
    for stock in stock_portfolio_information:
        if stock.type == 'Buy':
            numOfSharesOwned += stock.number_of_shares
        elif stock.type == 'Sell':
            numOfSharesOwned -= stock.number_of_shares
    
    return numOfSharesOwned

# Changes the Price of the Stocks
column_names = [
    'nine_thirty',
    'nine_forty_five',
    'ten',
    'ten_fifteen',
    'ten_thirty',
    'ten_forty_five',
    'eleven',
    'eleven_fifteen',
    'eleven_thirty',
    'eleven_forty_five',
    'twelve',
    'twelve_fifteen',
    'twelve_thirty',
    'twelve_forty_five',
    'one',
    'one_fifteen',
    'one_thirty',
    'one_forty_five',
    'two',
    'two_fifteen',
    'two_thirty',
    'two_forty_five',
    'three',
    'three_fifteen',
    'three_thirty',
    'three_forty_five',
    'four',
    'four_fifteen',
    'four_thirty'
]

def stock_price_generate():
    with app.app_context():
        while True:
            stocks = Stock.query.all()
            print(f"LENGTH IS {len(stocks)}")

            print("updating stocks1")

            for stock in stocks:
                stock.current_market_price += 1
                print("updating stocks")

            db.session.commit()

            time.sleep(10)

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

@app.route('/<stockname>/<username>', methods=['GET', 'POST'])
def stockviewer(username, stockname):
    user_information = User.query.filter_by(username=username).first()
    stock_information = Stock.query.filter_by(stock_name=stockname).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()

    # Calculating the Number of Shares Owned for the Stock Being Viewed
    numOfSharesOwned = calculate_shares_owned(user_information.id, stock_information.id)

    stockForm = TransactionStockForm(request.form)

    if request.method == 'POST':
        if 'submit' in request.form:
            if request.form['submit'] == 'Buy':
                numOfShares = stockForm.numOfShares.data
                total_amount = stock_information.current_market_price * numOfShares
                if stockForm.validate_on_submit():
                    if numOfShares > 0:
                        if total_amount <= portfolio_information.cash_balance:
                            if numOfShares <= stock_information.number_of_shares_to_purchase:
                                new_transaction = StockPortfolio (
                                    type = "Buy",
                                    price_per_share = stock_information.current_market_price,
                                    number_of_shares = numOfShares,
                                    total_amount = total_amount,
                                    stock_id = stock_information.id,
                                    user_id = user_information.id
                                )
                                portfolio_information.cash_balance -= total_amount
                                portfolio_information.stock_balance += total_amount
                                stock_information.number_of_shares_to_purchase -= numOfShares
                                db.session.add(new_transaction)
                                db.session.commit()
                                return redirect(url_for('stockviewer', username=username, stockname=stockname))
                            else:
                                flash('Error: Not Enough Shares to Purchase')
                        else:
                            flash('Error: Insufficient Funds')
                            return redirect(url_for('stockviewer', username=username, stockname=stockname))
                    else:
                        flash('Error: Please Enter in a Valid Number')
                        return redirect(url_for('stockviewer', username=username, stockname=stockname))
            elif request.form['submit'] == 'Sell':
                numOfShares = stockForm.numOfShares.data
                total_amount = stock_information.current_market_price * numOfShares
                if stockForm.validate_on_submit():
                    if numOfShares > 0:
                        if numOfShares <= numOfSharesOwned:
                            new_transaction = StockPortfolio (
                                type = "Sell",
                                price_per_share = stock_information.current_market_price,
                                number_of_shares = numOfShares,
                                total_amount = total_amount,
                                stock_id = stock_information.id,
                                user_id = user_information.id
                            )
                            portfolio_information.cash_balance += total_amount
                            portfolio_information.stock_balance -= total_amount
                            stock_information.number_of_shares_to_purchase += numOfShares
                            db.session.add(new_transaction)
                            db.session.commit()
                        else:
                            flash('Error: Insufficient Shares Owned')
                            return redirect(url_for('stockviewer', username=username, stockname=stockname))
                    else:
                            flash('Error: Please Enter in a Valid Number')
                            return redirect(url_for('stockviewer', username=username, stockname=stockname))

    return render_template('stockviewer.html', user_information=user_information, stock_information=stock_information, portfolio=portfolio_information, stockForm=stockForm, numOfSharesOwned=numOfSharesOwned)

@app.route('/portfolio/<username>')
def portfolio(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    return render_template('portoflio.html',user_information=user_information, portfolio=portfolio_information)

@app.route('/tradehistory/<username>')
def tradehistory(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('tradehistory.html', user_information=user_information)

@app.route('/accounttransfer/<username>', methods=['GET', 'POST'])
def accounttransfer(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    portfolio_transactions =  PortfolioTransaction.query.filter_by(portfolio_id=portfolio_information.id)

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
                            number_of_shares_to_purchase=createform.number_of_total_shares.data,
                            opening_price=createform.starting_market_price.data,
                            todays_high=createform.starting_market_price.data,
                            todays_low=createform.starting_market_price.data
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

if __name__ == "__main__":
    app.run(debug=True)