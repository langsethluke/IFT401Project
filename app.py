#Importing Flask and MySQL Libraries

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_wtf import FlaskForm 
from wtforms import StringField, FloatField, IntegerField, SubmitField, PasswordField, SelectField, TimeField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required
from decimal import Decimal
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import random
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from zoneinfo import ZoneInfo

app = Flask(__name__)

# Logs the User in
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

##################################
###### Setting Arizona Time ######
##################################

# Setting the time to Run the Stock Price Generator off of Arizona Time, No Matter Where the Machine is Running the Website is Located
# This will help because most of AWS servers are hosted on the east coast
# Function will recieve the Arizona Time each time the function is called

def get_current_time_date():

    # Setting Arizona Time
    az_time = datetime.now(ZoneInfo("America/Phoenix"))

    return az_time

print('Day', get_current_time_date().strftime("%A"))

##########################
###### MySQL Tables ######
##########################

# Defining the User Table
class User(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True) 
    first_name = db.Column(db.String(80), nullable=False) 
    last_name = db.Column(db.String(100), nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
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

    # Creating the relationship with Portfolio Value History Daily Table
    portfolio_value_history_daily = db.relationship('PortfolioValueHistoryDaily', back_populates='portfolio')

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
    date = db.Column(db.DateTime, default=get_current_time_date)

    #Creating the relationship with the Portofolio Table
    portfolio = db.relationship('Portfolio', back_populates='portfoliotransaction')

# Defining the Portfolio Value Daily History Table
class PortfolioValueHistoryDaily(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    nine_thirty = db.Column(db.Float)
    ten = db.Column(db.Float)
    ten_thirty = db.Column(db.Float)
    eleven = db.Column(db.Float)
    eleven_thirty = db.Column(db.Float)
    twelve = db.Column(db.Float)
    twelve_thirty = db.Column(db.Float)
    one = db.Column(db.Float)
    one_thirty = db.Column(db.Float)
    two = db.Column(db.Float)
    two_thirty = db.Column(db.Float)
    three = db.Column(db.Float)
    three_thirty = db.Column(db.Float)
    four = db.Column(db.Float)

    # Creating the relationship with the Portofolio Table
    portfolio = db.relationship('Portfolio', back_populates='portfolio_value_history_daily')

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
    percentage_change = db.Column(db.Float, nullable=False)

    # Creating the relationship with the StockPortfolio Table
    stock_portfolio = db.relationship('StockPortfolio', back_populates='stock', uselist=True)

    # Creating the relationship with the StockPriceHistoryDaily Table
    stock_price_history_daily = db.relationship('StockPriceHistoryDaily', back_populates='stock')

# Changes the total_market_cap column based off when the number_of_total_shares and current_market_price columns are changed
@event.listens_for(Stock, 'before_insert')
@event.listens_for(Stock, 'before_update')
def update_total_balance(mapper, connection, target):
        target.total_market_cap = target.current_market_price * target.number_of_total_shares

# Changes the precentage_change column based off when the opening_price and current_market_price columns are changed
@event.listens_for(Stock, 'before_insert')
@event.listens_for(Stock, 'before_update')
def update_precentage_change(mapper, connection, target):
        target.percentage_change = (Decimal(target.current_market_price) - Decimal(target.opening_price))/Decimal(target.opening_price) * 100

# Defining the Stock Price Daily History Table
class StockPriceHistoryDaily(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    nine_thirty = db.Column(db.Float)
    ten = db.Column(db.Float)
    ten_thirty = db.Column(db.Float)
    eleven = db.Column(db.Float)
    eleven_thirty = db.Column(db.Float)
    twelve = db.Column(db.Float)
    twelve_thirty = db.Column(db.Float)
    one = db.Column(db.Float)
    one_thirty = db.Column(db.Float)
    two = db.Column(db.Float)
    two_thirty = db.Column(db.Float)
    three = db.Column(db.Float)
    three_thirty = db.Column(db.Float)
    four = db.Column(db.Float)

    # Creating the relationship with the Stock Table
    stock = db.relationship('Stock', back_populates='stock_price_history_daily')

# Defining the Stock Portfolio Table
class StockPortfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(5), nullable=False)
    price_per_share = db.Column(db.Float(20,2), nullable=False)
    number_of_shares = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float(20,2), nullable=False)
    date = db.Column(db.DateTime, default=get_current_time_date)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Creating the relationship with the Stock Table
    stock = db.relationship('Stock', back_populates='stock_portfolio')

    # Creating the relationship with the User Table
    user = db.relationship('User', back_populates='stock_portfolio')

# Defining the Market Hours Table
class MarketHour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)
    open_time = db.Column(db.Time, nullable=True)  
    close_time = db.Column(db.Time, nullable=True)  

# Creates All Tables in the MySQL Server
with app.app_context(): db.create_all()

#############################################
##### Defining the Default Market Hours #####
#############################################

with app.app_context():

    if MarketHour.query.count() == 0:
        i = 1
        j = 0

        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        market_hours = []

        while i <= 7:
            print(i)

            print(days[j])

            # Setting the weekend days to no trading hours
            if days[j] == 'Sunday' or days[j] == 'Saturday':
                market_hour =  MarketHour (
                    day = days[j],
                    open_time = None,
                    close_time = None 
                )
            else:
                market_hour =  MarketHour (
                    day = days[j],
                    open_time = datetime.strptime("09:30:00", "%H:%M:%S").time(),
                    close_time = datetime.strptime("16:00:00", "%H:%M:%S").time() 
                )

            market_hours.append(market_hour)
            i+=1
            j+=1

        db.session.add_all(market_hours)
        db.session.commit()

#########################
###### Flask Forms ######
#########################

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

# Form for Setting the Market Hours
class MarketHourForm(FlaskForm):
    day_of_week = SelectField(
        'Day of the Week',
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday')
        ],
        validators=[DataRequired()]
    )

    open_time = TimeField('Market Open Time', validators=[DataRequired()])
    close_time = TimeField('Market Close Time', validators=[DataRequired()])
    submit = SubmitField('Set Market Hours')

#####################
##### Functions #####
#####################

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

# Helps define the if the market is open or closed
def is_market_open():
    current_day_of_week = get_current_time_date().strftime("%A")  

    if  current_day_of_week == "Sunday":
        return False

    market_hours = MarketHour.query.filter_by(day=current_day_of_week).first()

    if market_hours:
        current_time = datetime.now().time()
        if market_hours.open_time <= current_time <= market_hours.close_time:
            return True
        else:
            return False

def current_time_column():
    hour = get_current_time_date().hour
    minute = get_current_time_date().minute

    # Name of Columns in the Stock Price History and Porfolio History Table
    column_names = [
            ('nine_thirty', (9, 30)),
            ('ten', (10, 0)),
            ('ten_thirty', (10, 30)),
            ('eleven', (11, 0)),
            ('eleven_thirty', (11, 30)),
            ('twelve', (12, 0)),
            ('twelve_thirty', (12, 30)),
            ('one', (13, 0)),
            ('one_thirty', (13, 30)),
            ('two', (14, 0)),
            ('two_thirty', (14, 30)),
            ('three', (15, 0)),
            ('three_thirty', (15, 30)),
            ('four', (16, 0)),
        ]
    
    for column, (hour_col, min_col) in column_names:
        if (hour == hour_col and abs(minute - min_col) <= 5):
            return column
    return None

# Random Stock Price Generator and Updates the Stock User Portfolio
def stock_price_generate():
    with app.app_context():

        # Print statement so the user can see in the terminal when stock prices are being updated
        print("#####################################################\n############ Generating New Stock Prices ############\n#####################################################")

        stocks = Stock.query.all()
        users = User.query.all()
        user_portfolios = {user.id: Portfolio.query.filter_by(user_id=user.id).first() for user in users}

        for stock in stocks:
            stock_price_history_daily = StockPriceHistoryDaily.query.filter_by(stock_id=stock.id).first()

            # Generates the random float value between 0 and 0.50
            randfloatgen = random.random() * 0.50
            randfloat = round(randfloatgen, 2)

            # Deciding on either to add or subtract the generated float values
            rand1 = random.randint(0,1)

            if rand1 == 0:
                stock.current_market_price += Decimal(randfloat)
            elif rand1 == 1:
                stock.current_market_price -= Decimal(randfloat)

            # Ensures that the stock price will never dip below $0.00
            if stock.current_market_price <= 0:
                stock.current_market_price = Decimal(0.10)

            if stock.current_market_price > stock.todays_high:
                stock.todays_high = stock.current_market_price

            if stock.current_market_price < stock.todays_low:
                stock.todays_low = stock.current_market_price
            
            # Sets the stock price of a the stock price history column
            col_name = current_time_column()
            if col_name:
                setattr(stock_price_history_daily, col_name, stock.current_market_price)

            # Changes the stock_balance value in the user's portfolio table
            for user in users:
                portfolio = user_portfolios.get(user.id)

                if portfolio:
                    shares_owned = calculate_shares_owned(user.id, stock.id)
                    total = stock.current_market_price * shares_owned

                    if rand1 == 0:
                        portfolio.stock_balance += total
                    elif rand1 == 1:
                        portfolio.stock_balance -= total

        db.session.commit()

# Updates the Portfolio Value History for the User
def portfolio_value_history():
    with app.app_context():
        users = User.query.all()
        user_portfolios = {user.id: Portfolio.query.filter_by(user_id=user.id).first() for user in users}
        
        col_name = current_time_column()
        
        for user in users:
            portfolio = user_portfolios.get(user.id)

            if portfolio:
                portfolio_value_history = PortfolioValueHistoryDaily.query.filter_by(portfolio_id=portfolio.id).first()

                if col_name:
                        setattr(portfolio_value_history, col_name, portfolio.total_balance)

            db.session.commit()

# Resets the values in the history tables at the start of the day
def reset_value_history_tables():
    with app.app_context():
        stock_historys = StockPriceHistoryDaily.query.all()
        portfolio_historys = PortfolioValueHistoryDaily.query.all()

        for stock_history in stock_historys:
            stock_history.nine_thirty = None
            stock_history.ten = None
            stock_history.ten_thirty = None
            stock_history.eleven = None
            stock_history.eleven_thirty = None
            stock_history.twelve = None
            stock_history.twelve_thirty = None
            stock_history.one = None
            stock_history.one_thirty = None
            stock_history.two = None
            stock_history.two_thirty = None
            stock_history.three = None
            stock_history.three_thirty = None
            stock_history.four = None
        
        for portfolio_history in portfolio_historys:
            portfolio_history.nine_thirty = None
            portfolio_history.ten = None
            portfolio_history.ten_thirty = None
            portfolio_history.eleven = None
            portfolio_history.eleven_thirty = None
            portfolio_history.twelve = None
            portfolio_history.twelve_thirty = None
            portfolio_history.one = None
            portfolio_history.one_thirty = None
            portfolio_history.two = None
            portfolio_history.two_thirty = None
            portfolio_history.three = None
            portfolio_history.three_thirty = None
            portfolio_history.four = None

        db.session.commit()

# Sets the opening price for a stock 
def open_price():
    with app.app_context():
        stocks = Stock.query.all()
        for stock in stocks:
            stock.opening_price = stock.current_market_price
        
        db.session.commit()

# Create the schedulers and starts the random stock price generator
scheduler = BackgroundScheduler()

fiveMinuteTrigger = IntervalTrigger(minutes=5)
scheduledTrigger = CronTrigger(hour=1, minute=0)
scheduledTriggerOpenPrice = CronTrigger(hour=10, minute=30)

scheduler.add_job(stock_price_generate, fiveMinuteTrigger)
scheduler.add_job(portfolio_value_history, fiveMinuteTrigger)

# Resets the daily value history tables back to none at the start of the day
scheduler.add_job(reset_value_history_tables, scheduledTrigger)

# Sets the opening price of the day for each stock
scheduler.add_job(open_price, scheduledTriggerOpenPrice)

scheduler.start()

#################################
###### Creating Admin User ######
#################################

# Creating and commiting the admin user by setting the admin boolean value to 1
with app.app_context():
    admin = User.query.filter_by(username="admin").first()
    if admin == None:
        admin_user = User(first_name= 'Admin', last_name = 'Admin', username='admin', email='admin@goattrading.com', password=generate_password_hash('admin'), admin=1)
        db.session.add(admin_user)
        db.session.commit()

####################
###### Routes ######
####################

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        # Checking if the password matches the username
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged In Successfully!", "success")
            # If the user is a customer, it redirects them to their home page
            if user.admin == 0:
                return redirect(url_for('home', username=username))
            # If the user is an admin, it redirects to the admin home page
            elif user.admin == 1:
                return redirect(url_for('adminhome', username=username))
        else:
            flash("Invalid username or password", "error") 
    return render_template('login.html')

@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    userForm = UserForm()
    if userForm.validate_on_submit():

        # Check if the email already exists
        existing_email = User.query.filter_by(email=userForm.email.data).first()
        # Check if the username already exists
        existing_username = User.query.filter_by(username=userForm.username.data).first()

        # Check if the password confirmation is empty
        if not userForm.confirm.data:
            flash("Error: Password Not Repeated", "error")
            return render_template('createaccount.html', userForm=userForm)
        
        # Check if the password matches the confirmation
        if userForm.password.data != userForm.confirm.data:
            flash("Error: Passwords Not Matching", "error")
            return render_template('createaccount.html', userForm=userForm)
        
        # Generate the appropriate error message
        if existing_email and existing_username:
            flash("Error: An account with this Username and Email already exists", "error")
        elif existing_email:
            flash("Error: An account with this Email already exists", "error")
        elif existing_username:
            flash("Error: An account with this Username already exists", "error")
        # If any errors were flashed, reload the form
        if existing_email or existing_username:
            return render_template('createaccount.html', userForm=userForm)

        # Creates New User
        new_user = User( 
                        first_name=userForm.first_name.data, 
                        last_name=userForm.last_name.data, 
                        email=userForm.email.data, 
                        username=userForm.username.data, 
                        password=generate_password_hash(userForm.password.data) )
        
        # Commits the User first so the Portfolio can get a valid User ID
        db.session.add(new_user)
        db.session.commit()

        # Creates a Portfolio for the user
        new_portfolio = Portfolio(
                        total_balance = 0,
                        stock_balance = 0,
                        cash_balance = 0,
                        user_id = new_user.id )

        db.session.add(new_portfolio)
        db.session.commit()

        new_portfolio_value_history = PortfolioValueHistoryDaily (
            portfolio_id = new_portfolio.id
        )

        db.session.add( new_portfolio_value_history)
        db.session.commit()

        # Success message
        flash("Account created successfully!", "success")

        # Redirects to the login so the user can login
        return redirect(url_for('login'))
    return render_template('createaccount.html', userForm=userForm)

# Canceled Page for User accounts that are canceled in the creation process
@app.route('/accountcanceled')
def accountcanceled():
    return render_template('accountcanceled.html')

@app.route('/home/<username>')
def home(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    portfolio_value_history = PortfolioValueHistoryDaily.query.filter_by(portfolio_id=portfolio_information.id).first()

    hour = get_current_time_date().hour
    message = ""

    if hour >= 0 and hour < 12:
        message = "Good Morning"
    elif hour >= 12 and hour < 18:
        message = "Good Afternoon"
    elif hour >= 18:
        message = "Good Evening"

    return render_template('home.html', user_information=user_information, portfolio=portfolio_information, portfolio_value_history = portfolio_value_history, message=message)

@app.route('/adminhome/<username>')
def adminhome(username):
    user_information = User.query.filter_by(username=username).first()
    return render_template('adminhome.html', user_information=user_information)

@app.route('/trade/<username>')
def trade(username):
    stocks = Stock.query.all()
    user_information = User.query.filter_by(username=username).first()

    # Getting the current day of the week
    current_day_of_week = get_current_time_date().strftime("%A")
    market_hours = MarketHour.query.filter_by(day=current_day_of_week).first()

    # Checking if the market is open or closed
    market_status = is_market_open()

    return render_template('trade.html', user_information=user_information, stocks=stocks, market_hours=market_hours, market_status=market_status)

@app.route('/<stockname>/<username>', methods=['GET', 'POST'])
def stockviewer(username, stockname):
    user_information = User.query.filter_by(username=username).first()
    stock_information = Stock.query.filter_by(stock_name=stockname).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    stock_price_history_information = StockPriceHistoryDaily.query.filter_by(stock_id=stock_information.id).first()

    # Checking if the market is open or closed
    market_status = is_market_open()

    # Calculating the Number of Shares Owned for the Stock Being Viewed
    numOfSharesOwned = calculate_shares_owned(user_information.id, stock_information.id)

    stockForm = TransactionStockForm(request.form)

    if request.method == 'POST':
        if 'submit' in request.form:
            numOfShares = stockForm.numOfShares.data
            if stockForm.validate_on_submit():

                # Buying a Stock
                if request.form['submit'] == 'Buy':
                    #numOfShares = stockForm.numOfShares.data
                    total_amount = stock_information.current_market_price * numOfShares
                    if numOfShares <= 0:
                        flash("Error: Number of Shares Cannot be Negative", "danger")
                    elif total_amount > portfolio_information.cash_balance:
                        flash("Error: Insufficient Funds", "danger")
                    elif numOfShares > stock_information.number_of_shares_to_purchase:
                        flash("Error: Not Enough Shares to Purchase", "danger")
                    else:
                        # Execute Purchase
                        new_transaction = StockPortfolio(
                            type="Buy",
                            price_per_share=stock_information.current_market_price,
                            number_of_shares=numOfShares,
                            total_amount=total_amount,
                            stock_id=stock_information.id,
                            user_id=user_information.id
                        )

                        portfolio_information.cash_balance -= total_amount
                        portfolio_information.stock_balance += total_amount
                        stock_information.number_of_shares_to_purchase -= numOfShares

                        db.session.add(new_transaction)
                        db.session.commit()

                        flash("Transaction Successful", "success")
                        return redirect(url_for('stockviewer', username=username, stockname=stockname))

                # Selling Stock
                elif request.form['submit'] == 'Sell':
                    #numOfShares = stockForm.numOfShares.data
                    total_amount = stock_information.current_market_price * numOfShares
                    if numOfShares <= 0:
                        flash("Error: Number of Shares Cannot be Negative", "danger")
                    elif numOfShares > numOfSharesOwned:
                        flash("Error: Insufficient Shares", "danger")
                    else:
                        # Execute Sale
                        new_transaction = StockPortfolio(
                            type="Sell",
                            price_per_share=stock_information.current_market_price,
                            number_of_shares=numOfShares,
                            total_amount=total_amount,
                            stock_id=stock_information.id,
                            user_id=user_information.id
                        )
                        portfolio_information.cash_balance += total_amount
                        portfolio_information.stock_balance -= total_amount
                        stock_information.number_of_shares_to_purchase += numOfShares
                        db.session.add(new_transaction)
                        db.session.commit()
                        flash("Transaction Successful", "success")
                        return redirect(url_for('stockviewer', username=username, stockname=stockname))

    return render_template('stockviewer.html', user_information=user_information, stock_information=stock_information, portfolio=portfolio_information, stockForm=stockForm, numOfSharesOwned=numOfSharesOwned, stock_price_history_information=stock_price_history_information, market_status=market_status)

@app.route('/portfolio/<username>')
def portfolio(username):
    user_information = User.query.filter_by(username=username).first()
    portfolio_information = Portfolio.query.filter_by(user_id=user_information.id).first()
    stock_information = Stock.query.all()
    portfolio_value_history = PortfolioValueHistoryDaily.query.filter_by(portfolio_id=portfolio_information.id).first()

    numOfSharesOwned = {}
    for stock in stock_information:
        numOfSharesOwned[stock.id] = calculate_shares_owned(user_information.id, stock.id)

    stocks_owned_by_user = [stock for stock in stock_information 
                            if numOfSharesOwned[stock.id] > 0]

    return render_template('portoflio.html',user_information=user_information, portfolio=portfolio_information, stock_information = stock_information, numOfSharesOwned = numOfSharesOwned, stocks_owned_by_user=stocks_owned_by_user, portfolio_value_history = portfolio_value_history)

@app.route('/tradehistory/<username>')
def tradehistory(username):
    user_information = User.query.filter_by(username=username).first()
    stock_portfolio_information = StockPortfolio.query.filter_by(user_id=user_information.id).all()
    return render_template('tradehistory.html', user_information=user_information, stock_portfolio_information=stock_portfolio_information)

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

                    flash("Deposit Successful", "success")
                    return redirect(url_for('accounttransfer', username=username))
            elif request.form['submit'] == 'Withdraw':
                amount = Decimal(withdrawForm.amount.data)
                if withdrawForm.validate_on_submit():
                    if amount <= portfolio_information.cash_balance:
                        new_transaction = PortfolioTransaction (
                            type = "Withdraw",
                            amount = amount,
                            portfolio_id = portfolio_information.id
                            )
                        portfolio_information.cash_balance -= amount

                        db.session.add(new_transaction)
                        db.session.commit()

                        flash("Withdrawal Successful", "success")
                        return redirect(url_for('accounttransfer', username=username))
                    else:
                        flash("Error: Insufficient Funds", "error")

    return render_template('accounttransfer.html', user_information=user_information, portfolio=portfolio_information, depositForm=depositForm, withdrawForm=withdrawForm, portfolio_transactions=portfolio_transactions)

@app.route('/adminstocks/<username>', methods=['GET', 'POST'])
def adminstocks(username):
    user_information = User.query.filter_by(username=username).first()
    stocks = Stock.query.all()

    createform = StockForm()

    if createform.validate_on_submit():
        # Validation for existing stocks
        existing_name = Stock.query.filter_by(stock_name=createform.stock_name.data).first()
        existing_ticker = Stock.query.filter_by(ticker_symbol=createform.ticker_symbol.data).first()
        if existing_name:
            flash("Error: Stock Name Already Exists", "error")
        elif existing_ticker:
            flash("Error: Ticker Symbol Already Exists", "error")
        elif createform.number_of_total_shares.data < 1:
            flash("Error: Number of Shares Cannot Be Less Than Zero", "error")
        elif createform.starting_market_price.data < 1:
            flash("Error: Price Cannot Be Negative", "error")
        else:
            # Create the stock if all validations pass
            new_stock = Stock(
                stock_name=createform.stock_name.data,
                ticker_symbol=createform.ticker_symbol.data,
                starting_market_price=createform.starting_market_price.data,
                current_market_price=createform.starting_market_price.data,
                number_of_total_shares=createform.number_of_total_shares.data,
                number_of_shares_to_purchase=createform.number_of_total_shares.data,
                opening_price=createform.starting_market_price.data,
                todays_high=createform.starting_market_price.data,
                todays_low=createform.starting_market_price.data,
            )
            
            db.session.add(new_stock)
            db.session.commit()

            new_stock_price_history = StockPriceHistoryDaily(stock_id=new_stock.id)

            db.session.add(new_stock_price_history)
            db.session.commit()

            flash("Stock Created Successfully", "success")
            return redirect(url_for('adminstocks', username=username))

    return render_template('adminstocks.html', user_information=user_information, createform=createform, stocks=stocks)

@app.route('/adminmarkethours/<username>', methods=['GET', 'POST'])
def adminmarkethours(username):
    user_information = User.query.filter_by(username=username).first()

    # Gets the current day of the week
    current_day_of_week = get_current_time_date().strftime("%A")
    market_hours = MarketHour.query.filter_by(day=current_day_of_week).first()

    all_market_hours = MarketHour.query.all()

    # Checking if the market is open or closed
    market_status = is_market_open()

    form = MarketHourForm()

    if form.validate_on_submit():
        day_of_the_week = form.day_of_week.data
        open_time = form.open_time.data
        close_time = form.close_time.data

        market_hours_day = MarketHour.query.filter_by(day=day_of_the_week).first()

        if market_hours_day:
            market_hours_day.open_time = open_time
            market_hours_day.close_time = close_time
            db.session.commit()
            flash("Market Hours Updated Successfully", "success")
            return redirect(url_for('adminmarkethours', username=username))
    return render_template('adminmarkethours.html', user_information=user_information, form=form, market_hours=market_hours, market_status=market_status, all_market_hours=all_market_hours)   

#########################
###### HTMX Routes ######
#########################

# These routes help get data from the MySQL server so that the variables on the frontend can be updated dynamically without the user to have to refresh the page

@app.route('/get_stock_price/<stock_id>')
def get_stock_price(stock_id):
    stock = Stock.query.get(stock_id)
    if stock:
        return f"${stock.current_market_price:.2f}"
    
@app.route('/get_percentage_change/<stock_id>')
def get_percentage_change(stock_id):
    stock = Stock.query.get(stock_id)
    if stock:
        if stock.percentage_change >= 0:
            color='green'
            return f"<span style='color:{color};'>+{stock.percentage_change:.2f}%</span>"
        if stock.percentage_change < 0:
            color='red'
            return f"<span style='color:{color};'>{stock.percentage_change:.2f}%</span>"

@app.route('/get_portfolio_total_value/<user_id>')
def get_portfolio_total_value(user_id):
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    return f"<span>${portfolio.total_balance:.2f}</span>"

######################
##### API Routes #####
######################

@app.route('/api/stocks')
def get_stocks():
    stocks = Stock.query.all()
    stock_data = [{"id": f"stock-{stock.id}", "ticker": stock.ticker_symbol, "percentage": stock.percentage_change, "name": stock.stock_name} for stock in stocks] 
    sorted_stocks = sorted(stock_data, key=lambda x: x['percentage'], reverse=True)
    top_performers = sorted_stocks[:5]
    low_performers = sorted_stocks[-5:]
    return jsonify({
        'top_performers': top_performers,
        'low_performers': low_performers
    })
        
if __name__ == "__main__":
    app.run(debug=True)