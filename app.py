from flask import Flask, redirect, render_template, request
from flask_admin import BaseView, Admin, expose
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib import sqla

# Create flask app
app = Flask(__name__, template_folder='templates')
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = 'PizzaPi3sIsG00d'

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


# Network section ##
class NetworkSQL(db.Model):
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
        device_each = NetworkSQL()

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

        db.session.commit()


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


@app.route('/build')
def building():
    build_live_list()
    return redirect('admin/networksql')


@app.route('/n/segment')
def tesingpath():
    names = request.args.get('name')
    return render_template('octets.html', names=names)


@app.route('/segment')
def segmentSQL():
    names = NetworkSQL.query.all()
    return render_template('octets.html', names=names)


# Create custom admin view
class MyView(BaseView):
    @expose('/')
    def index(self):
        name = "bob"
        return self.render('myadmin.html', name=name)


# Create admin interface
admin = Admin(name="Pacman", template_mode='bootstrap3')
admin.add_view(MyView(name='My View', menu_icon_type='glyph', menu_icon_value='glyphicon-home'))
admin.add_view(NetworkModel(NetworkSQL, db.session))
admin.add_view(SegmentModel(SegmentSQL, db.session))

admin.init_app(app)

if __name__ == '__main__':
    import nmap3

    nmap3.starting()

    # Create DB
    db.create_all()

    # Start app
    app.run(host='127.0.0.1', port=5001)
