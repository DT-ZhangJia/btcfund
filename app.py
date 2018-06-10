"""
learn flask
"""
# pylint: disable=invalid-name
from flask_bootstrap import Bootstrap 
from flask_script import Manager, Shell
from flask import Flask, url_for, redirect, request, render_template, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct, func
from binance.client import Client
from urllib import parse, request
from config import config
import json


app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)
app.config.from_object(config['default'])
app.config.from_pyfile('config.py') #密钥类设置不能开源存入config.py
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True #True无需session.commit()即可直接操作写入数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

mydb = SQLAlchemy(app)



class Btc(mydb.Model):
    __tablename__ = 'btc'
    idbtc = mydb.Column(mydb.Integer, primary_key=True, unique=True, index=True)
    symbol = mydb.Column(mydb.String(45))
    amount = mydb.Column(mydb.Float)
    date = mydb.Column(mydb.Date)
    cnycost = mydb.Column(mydb.Float)


class Base(mydb.Model):
    __tablename__ = 'base'
    iddd = mydb.Column(mydb.Integer, primary_key=True, unique=True, index=True)
    invest = mydb.Column(mydb.Float)
    date = mydb.Column(mydb.Date)




def make_shell_context():
    return dict(sapp=app, smydb=mydb)#shell命令起名
manager.add_command("shell", Shell(make_context=make_shell_context))



@app.route('/', methods=['GET', 'POST']) 
def index():
    client = Client(app.config['API_KEY'] , app.config['API_SECRET'] )
    prices = client.get_all_tickers()


    url='http://data.fixer.io/api/latest?access_key=87fdd450a053ec762d421382f62b7ad7&symbols=USD,CNY'
    req = request.Request(url)
    res = request.urlopen(req)
    res = res.read()
    resjson = json.loads(res)
    usdrate = resjson["rates"]["USD"]
    cnyrate = resjson["rates"]["CNY"]
    fex = float(cnyrate/usdrate)

    mybtc = mydb.session.query(Btc.symbol, func.sum(Btc.amount).label('amount'), func.sum(Btc.cnycost).label('cnycost')).group_by(Btc.symbol).all()
    mybase = mydb.session.query(func.sum(Base.invest).label('invest')).first()
    mybaseinvest = mybase.invest

    portfolio = {}

    mybtclist = {}
    for symbol in prices:
        mybtclist[symbol['symbol']]=symbol['price']


    cnysum = float(0)
    for coin in mybtc:
        if coin.symbol+"USDT" in mybtclist:
            cnyprice = float(mybtclist[coin.symbol+"USDT"])*fex#*float(coin.amount)
            portfolio[coin.symbol] = [coin.amount, coin.cnycost, round(float(coin.cnycost)/float(coin.amount),2), cnyprice, round(cnyprice,2),round((cnyprice*float(coin.amount)-float(coin.cnycost))/(float(coin.cnycost))*100,2)]
        elif coin.symbol+"ETH" in mybtclist:
            cnyprice = float(mybtclist[coin.symbol+"ETH"])*float(mybtclist['ETHUSDT'])*fex#*float(coin.amount)
            portfolio[coin.symbol] = [coin.amount, coin.cnycost, round(float(coin.cnycost)/float(coin.amount),2), cnyprice, round(cnyprice,2),round((cnyprice*float(coin.amount)-float(coin.cnycost))/(float(coin.cnycost))*100,2)]
        else:
            cnyprice = float(mybtclist[coin.symbol+"BTC"])*float(mybtclist['BTCUSDT'])*fex#*float(coin.amount)
            portfolio[coin.symbol] = [coin.amount, coin.cnycost, round(float(coin.cnycost)/float(coin.amount),2), cnyprice, round(cnyprice,2),round((cnyprice*float(coin.amount)-float(coin.cnycost))/(float(coin.cnycost))*100,2)]
        cnysum = cnysum+float(portfolio[coin.symbol][3]*float(coin.amount))

    gain = round((cnysum/float(mybaseinvest)-1)*100,2)

    cnysumround = float('%.2f' % cnysum)
    mybaseinvestround = float('%.2f' % mybaseinvest)

    return render_template('index.html', prices=prices,fex=fex, mybtc=mybtc, portfolio=portfolio, cnysumround=cnysumround, mybaseinvestround=mybaseinvestround, gain=gain)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__': 
    #app.run(host="0.0.0.0",port=8080,debug=True,ssl_context='adhoc') #程序实例的run方法用以启动
    manager.run()#用命令行调用并指定参数：python3 app.py runserver -h 0.0.0.0 -p 8080
