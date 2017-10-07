from flask import Flask, redirect, render_template, request, url_for
from flask_admin import BaseView, Admin, expose
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib import sqla
import flask_wtf

# Create flask app
app = Flask(__name__, template_folder='templates')
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = 'PizzaPi3sIsG00d'
app.config['CSRF_ENABLED'] = True

flask_wtf.CsrfProtect(app)

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db_001.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.debug = True


#  Saving the Segments for easy access
class SegmentSQL(db.Model):
    __tablename__ = 'segments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(11))
    created_on = db.Column(db.DateTime, server_default=db.func.now())

    def __str__(self):
        return self.desc


class SegmentModel(sqla.ModelView):
    column_display_pk = False  # Controls if the primary key should be displayed in the list view.
    column_searchable_list = ['id', 'ip_address']
    form_columns = ['id', 'ip_address', 'created_on']

    form_widget_args = {
        'created_on': {
            'disabled': True
        }
    }


class IPAddressLogs(db.Model):
    __tablename__ = 'ipAddressChangeLogs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(25))  # unique=False
    ip_address = db.Column(db.String(25))  # unique=False
    notes = db.Column(db.String(50))
    created_on = db.Column(db.DateTime, server_default=db.func.now())

    def __str__(self):
        return self.desc


# Four Octets - Network ##
class NetworkFourOctetsSQL(db.Model):
    __tablename__ = 'deviceNames'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(25))  # unique=False
    location = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime(), server_default=db.func.now(), onupdate=db.func.now())

    def __str__(self):
        return self.desc


class NetworkModel(sqla.ModelView):
    column_display_pk = False  # Controls if the primary key should be displayed in the list view.
    column_searchable_list = ['device_name', 'ip_address']
    form_columns = ['device_name', 'location', 'ip_address', 'created_on', 'updated_on']

    form_widget_args = {
        'desc': {
            'rows': 10,
            'style': 'color: red'
        },
        'created_on': {
            'disabled': True
        }, 'updated_on': {
            'disabled': True
        }
    }


def build_live_list():
    import nmap3

    db.drop_all()
    db.create_all()

    scanned_results = nmap3.starting()
    s = nmap3.location_saved_results(scanned_results)

    #  print(s.read())
    each_line_scanned = nmap3.filter_names(s)

    for more in each_line_scanned[:5]:
        device_each = NetworkFourOctetsSQL()

        if more['Device'] is str("DHCP"):
            device_each.device_name = " "
        else:
            device_each.device_name = more['Device']

        # Join list[xxx, xxx, xxx, xxx]
        ip = ".".join(more['IP'])

        device_each.ip_address = ip
        device_each.location = "N/A"
        db.session.add(device_each)

        #  Scan for liveNetwork segment...must not have duplicates
        seg = SegmentSQL()
        unique_segment = ".".join(more['IP'][:3])  # Only the first 3 octets
        seg.ip_address = unique_segment

        testing_setting = db.session.query(SegmentSQL).filter_by(ip_address=unique_segment).first()

        if not testing_setting:
            db.session.add(seg)

        # Creating log - for each added device #


        # Commit your request
        db.session.commit()


# PRAGMA table_info(deviceNames);
#  UPDATE deviceNames SET device_name='cocsws142000' WHERE id=4

# Flask views
@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        message = request.form['location']
        return '<a href="/admin/">Click me to get to Admin!{}</a>'.format(message)
    else:
        a = request.args.get('location', None)
        return '<a href="/admin/">Click me to get to Admin!{}</a>'.format(a)


@app.route('/build')
def building():
    build_live_list()
    return redirect('admin/networksql')


@app.route('/mapSegments')
def segmentSQL():
    names = SegmentSQL.query.all()
    url = "./map"
    return render_template('mapSegments.html', names=names, url=url)


@app.route('/map/<x>')
def map_octets(x):
    names = db.engine.execute("SELECT * FROM {} WHERE ip_address LIKE '{}%'".format('deviceNames', x))
    url = "../segment"
    return render_template('mapSegments.html', names=names, url=url)


@app.route('/success/<name>')
def success(name):
    return 'welcome %s' % name


@app.route('/segment/<four_octets>', methods=('GET', 'POST'))
def device_octets_path(four_octets):
    if request.method == 'POST':
        y = NetworkFourOctetsSQL()
        y.location = request.form['location']
        y.device_name = request.form['device']
        db.session.add(y)
        db.session.commit()
        return redirect(url_for('success', name=y.location))

    if request.method == 'GET':
        open_conn = db.engine.execute(
            "SELECT * FROM {} WHERE {}='{}' LIMIT 1".format("deviceNames", "ip_address", four_octets))
        x = open_conn

    return render_template('fouroctets.html', x=x)


# Create custom admin view
class MyView(BaseView):
    @expose('/')
    def index(self):
        name = "bob"
        return self.render('myadmin.html', name=name)


# Create admin interface
admin = Admin(name="Pacman", template_mode='bootstrap3')
admin.add_view(MyView(name='My View', menu_icon_type='glyph', menu_icon_value='glyphicon-home'))
admin.add_view(NetworkModel(NetworkFourOctetsSQL, db.session))
admin.add_view(SegmentModel(SegmentSQL, db.session))

admin.init_app(app)

if __name__ == '__main__':
    import nmap3

    nmap3.starting()

    # Create DB
    # build_live_list()
    db.create_all()

    # Start app
    app.run(host='127.0.0.1', port=5001)
