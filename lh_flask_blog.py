from flask import Flask , render_template, session, redirect, url_for, flash
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message
import os
from threading import Thread

basedir = os.path.abspath(os.path.dirname(__file__))


class NameForm(FlaskForm):
    name = StringField('what is your name?', validators=[Required()])
    submit = SubmitField('Submit')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string' #防止CSRF攻击，用WTF设置一个密钥用来验证表单数据的真伪
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'mysql://user_django:liaoheng@127.0.0.1/flask_blog'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = '465'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USER_SSL'] = True
app.config['MAIL_USERNAME'] = 'lostforsaya@qq.com'
app.config['MAIL_PASSWORD'] = 'hisavycxlfssbiia'
app.config['FLASKY_ADMIN'] = 'liaoheng.lh@alibaba-inc.com'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <lostforsaya@qq.com>'
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
"""
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'lostforsaya@qq.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'hisavycxlfssbiia')
FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
FLASKY_MAIL_SENDER = 'Flasky Admin <lostforsaya@qq.com>'
FLASKY_ADMIN = os.environ.get('FLASK_ADMIN', 'liaoheng.lh@alibaba-inc.com')
"""

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager.add_command('db', MigrateCommand)
mail = Mail(app)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to ,subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


"""
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():  ##检查输入内容是否符合验证
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name !')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html',  form = form, name=session.get('name'),
                           current_time=datetime.utcnow())
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'NEW User', 'mail/new_user' ,user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False), current_time=datetime.utcnow())





@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)





if __name__ == '__main__':
    app.run(debug=True)

"""
 $ python hello.py
     usage: hello.py [-h] {shell,runserver} ...
 positional arguments:
  {shell,runserver}
    shell
    runserver
optional arguments:
  -h, --help
在Flask应用上下文中运行Python shell 运行 Flask 开发服务器:app.run()
显示帮助信息并退出


(venv) $ python
     >>> from hello import app
     >>> app.url_map
     Map([<Rule '/' (HEAD, OPTIONS, GET) -> index>,
<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>, <Rule '/user/<name>' (HEAD, OPTIONS, GET) -> user>])

"""