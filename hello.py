"""
learn flask
"""
# pylint: disable=invalid-name
import os
from flask_bootstrap import Bootstrap #得先导入Bootsrtap
from flask_script import Manager, Shell
from flask import Flask, url_for, redirect, request, render_template, session, flash
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm# as Form
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message
from binance.client import Client
from urllib import parse, request
from config import config

#from config import config

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)#教程貌似没跟我说要加这段啊！
moment = Moment(app)#这种把函数套一层的手法是啥意思啊，让函数内获得新的方法？
#app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
#app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') 
app.config.from_object(config['default'])
app.config.from_pyfile('config.py') #密钥类设置不能开源存入config.py
#SECRET_KEY
#SQLALCHEMY_DATABASE_URI
#MAIL_USERNAME
#MAIL_PASSWORD
#FLASKY_ADMIN
#FLASKY_MAIL_SENDER
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True #True无需session.commit()即可直接操作写入数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'


#app.config.from_object(config['MAIL_USERNAME'])
#app.config.from_object(config['MAIL_PASSWORD'])

mydb = SQLAlchemy(app)
mail = Mail(app)




class Btc(mydb.Model):
    __tablename__ = 'btc'
    idbtc = mydb.Column(mydb.Integer, primary_key=True, unique=True, index=True)
    symbol = mydb.Column(mydb.String(45))
    amount = mydb.Column(mydb.Float)
    date = mydb.Column(mydb.Date)

class Base(mydb.Model):
    __tablename__ = 'base'
    iddd = mydb.Column(mydb.Integer, primary_key=True, unique=True, index=True)
    invest = mydb.Column(mydb.Float)




def make_shell_context():
    return dict(sapp=app, smydb=mydb, sUser=User, sRole=Role)#shell命令起名
manager.add_command("shell", Shell(make_context=make_shell_context))#不明白这句话

migrate = Migrate(app, mydb)
manager.add_command('sdb', MigrateCommand)





def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)



#处理一个URL和Python函数之间映射关系的程序称为路由。
@app.route('/', methods=['GET', 'POST']) #这是flask内置的装饰器可以把函数注册为路由
def index():
    client = Client(app.config['API_KEY'] , app.config['API_SECRET'] )
    prices = client.get_all_tickers()


    url='https://api.fixer.io/latest?base=USD'
    req = request.Request(url)
    res = request.urlopen(req)
    res = res.read()
    fex = float(eval(res)['rates']['CNY'])

    mybtc = Btc.query.all()
    mybase = Base.query.first()
    mybaseinvest = mybase.invest

    portfolio = {}

    mybtclist = {}
    for symbol in prices:
        mybtclist[symbol['symbol']]=symbol['price']

    cnysum = float(0)
    for coin in mybtc:
        if coin.symbol+"USDT" in mybtclist:
            portfolio[coin.symbol] = [coin.amount,float(mybtclist[coin.symbol+"USDT"])*float(coin.amount)*fex]
        elif coin.symbol+"ETH" in mybtclist:
            portfolio[coin.symbol] = [coin.amount,float(mybtclist[coin.symbol+"ETH"])*float(mybtclist['ETHUSDT'])*float(coin.amount)*fex]
        else:
            portfolio[coin.symbol] = [coin.amount,float(mybtclist[coin.symbol+"BTC"])*float(mybtclist['BTCUSDT'])*float(coin.amount)*fex]
        cnysum = cnysum+portfolio[coin.symbol][1]

    gain = round((cnysum/float(mybaseinvest)-1)*100,2)

    cnysumround = float('%.2f' % cnysum)
    mybaseinvestround = float('%.2f' % mybaseinvest)

    return render_template('index.html', prices=prices,fex=fex, mybtc=mybtc, portfolio=portfolio, cnysumround=cnysumround, mybaseinvestround=mybaseinvestround, gain=gain)
    #pyname = None#初始化id为空
    """
    pyform = NameForm()
    if pyform.validate_on_submit():#验证的是required参数
        #pyname = pyform.indexname.data
        usercheck = User.query.filter_by(username=pyform.indexname.data).first()
        if usercheck is None:
            session['exist'] = False
            newuser = User(username=pyform.indexname.data, role_id=3)#建立新用户记录
            mydb.session.add(newuser)#新记录写入数据库操作
            #if app.config['FLASKY_ADMIN']:#通知管理员新用户
            send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', mailuser=newuser)
        else:
            session['exist'] = True
        old_name = session.get('pyname')
        if old_name is not None and old_name != pyform.indexname.data:
            flash('name changed.')
        session['pyname'] = pyform.indexname.data
        #pyform.indexname.data = ''
        #return redirect(url_for('user', name=pyname))#终于用上了url_for函数！
        return redirect(url_for('index'))
    return render_template('index.html', indexform=pyform,
                           indexname2=session.get('pyname'),
                           exist_index=session.get('exist', False),
                           current_time=datetime.utcnow())
#注意这里的参数设置，程序内的form变量名（pyform）模板内的form变量名（indeform）
    #return render_template('index.html')#使用模板响应视图函数
    """


#尖括号中的内容就是动态部分，任何能匹配静态部分的URL都会映射到这个路由上。
#调用视图函数时，Flask会将动态部分作为参数传入函数。
@app.route('/user/<name>') #把可变参数的地址注册为一个新的路由
def user(name):
    return render_template('user.html', usr=name,
                           current_time=datetime.utcnow())#模板及变量传入视图函数
    #return '<h1>Hello, %s!</h1>' % name
#用request产生临时的视图

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/browser')
def browser():
    user_agent = request.headers.get('User-Agent') #
    return '<p>Your browser is %s</p>' % user_agent

@app.route('/comments')
def comments():
    all_comments = ["good job!", "great!", "i like it!", "not bad!"]
    return render_template('comments.html',comments=all_comments) #传入list，让模板执行macro。

#重定向是一种响应，内置函数

@app.route('/zhihu')
def zhihu():
    return redirect('http://www.zhihu.com')




if __name__ == '__main__': #用这项条件来确保自身文件执行才执行
    #app.run(host="0.0.0.0",port=8080,debug=True,ssl_context='adhoc') #程序实例的run方法用以启动
    manager.run()#用命令行调用并指定参数：python3 hello.py runserver -h 0.0.0.0 -p 8080
