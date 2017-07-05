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


class NetworkDevices(db.Model):
    __tablename__ = 'deviceNames'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(25))  # unique=False
    location = db.Column(db.String(50))
    desc = db.Column(db.String(50))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime(), server_default=db.func.now(), onupdate=db.func.now())

    def __str__(self):
        return self.desc


class NetworkAdmin(sqla.ModelView):
    column_display_pk = False  # Controls if the primary key should be displayed in the list view.
    column_searchable_list = ['device_name', 'desc']
    form_columns = ['device_name', 'location', 'desc', 'created_on', 'updated_on']

    form_widget_args = {
        'desc': {
            'rows': 10,
            'style': 'color: red'
        }
    }

    form_widget_args = {
        'created_on': {
            'disabled': True
        }, 'updated_on': {
            'disabled': True
        }
    }

    def create_form(self):
        form = NetworkDevices()
        form.vendor.query = device_name.query.all()
        return form


def build_live_list():
    import nmap3

    db.drop_all()
    db.create_all()

    scanned_results = nmap3.starting()
    s = nmap3.location_saved_results(scanned_results)

    #  print(s.read())
    each_line_scanned = nmap3.filter_names(s)

    for more in each_line_scanned[45:60]:
        each = NetworkDevices()
        each.device_name = more['Device']

        #  Join list[xxx, xxx, xxx, xxx]
        ip = ".".join(more['IP'])
        each.desc = ip

        each.location = "N/A"
        db.session.add(each)
        db.session.commit()


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


@app.route('/build')
def building():
    build_live_list()
    return redirect('admin/networkdevices')


# Create custom admin view
class MyAdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('myadmin.html')


# Create admin interface
admin = Admin(name="Pacman", template_mode='bootstrap3')
admin.add_view(NetworkAdmin(NetworkDevices, db.session))
admin.add_view(MyAdminView(name="Accounts", category='Custom'))
admin.init_app(app)

if __name__ == '__main__':
    import nmap3

    nmap3.starting()

    # Create DB
    db.create_all()

    # Start app
    app.run(host='127.0.0.1', port=5000)
