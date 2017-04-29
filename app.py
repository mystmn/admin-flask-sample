from flask import Flask, redirect, url_for
from flask_admin import BaseView, Admin, expose
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib import sqla

import random

# Create flask app
app = Flask(__name__, template_folder='templates')
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = 'PizzaPi3sIsG00d'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db_001.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.debug = True


# Create custom admin view
class MyAdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('myadmin.html')


class NetworkDevices(db.Model):
    __tablename__ = 'deviceNames'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(25), unique=True)
    location = db.Column(db.String(50))
    desc = db.Column(db.String(50))

    def __str__(self):
        return self.desc


class NetworkAdmin(sqla.ModelView):
    column_display_pk = False  # Controls if the primary key should be displayed in the list view.
    column_searchable_list = ['device_name']
    form_columns = ['device_name', 'location', 'desc']


def build_sample():
    each = NetworkDevices()
    each.device_name = "coehws{}".format(random.randrange(100000, 900000))
    each.location = "coffeeShop"
    each.desc = "Last Table"
    db.session.add(each)
    db.session.commit()


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


@app.route('/build')
def building():
    build_sample()
    return redirect('admin/networkdevices')


# Create admin interface
admin = Admin(name="Pacman", template_mode='bootstrap3')
admin.add_view(NetworkAdmin(NetworkDevices, db.session))
admin.add_view(MyAdminView(name="Accounts", category='Custom'))
admin.init_app(app)

if __name__ == '__main__':
    # Create DB
    db.create_all()

    # Start app
    app.run(host='127.0.0.1', port=5002)
