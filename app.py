from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/trade')
def trade():
    return render_template('trade.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portoflio.html')

@app.route('/tradinghistory')
def tradinghistory():
    return render_template('tradinghistory.html')

@app.route('/accounttransfer')
def accounttransfer():
    return render_template('accounttransfer.html')

@app.route('/adminstocks')
def adminstocks():
    return render_template('adminstocks.html')

@app.route("/create_account")
def create_account(): 
    return render_template('create_account.html')

if __name__ == "__main__": app.run(debug=True)