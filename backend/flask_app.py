from flask import Flask, flash, redirect, url_for, render_template, request, session, jsonify, Blueprint
from datetime import timedelta, time
from sqlalchemy import func
import dateutil
from model import RideUser, Ride, db, Ride_Archive, User, College, Location
from flask_migrate import Migrate
import json
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from token_creator import generate_confirmation_token, confirm_token
from email_sender import send_email
from flask_mail import Mail, Message
#import uuid
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, redirect
from api_routes import api_route
from flask_cors import CORS
import os

app = Flask(__name__)
app.config.from_object('config.Config')  # Load configuration from config.py

mail = Mail(app)
#if (app.config ['ENVIRONMENT'] == 'dev'):
#    print('Development env. NO CORS')
#else:
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, supports_credentials=True, expose_headers=['Authorization'])

app.permanent_session_lifetime = timedelta(days=30)
print(app.config ['SQLALCHEMY_DATABASE_URI'])
if (app.config ['ENVIRONMENT'] == 'dev'):
     print('Development Environment')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

jwt = JWTManager(app)

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGER_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name' : "Todo List API"
    }
)

app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=SWAGGER_URL)

login_manager = LoginManager() # Add this line
login_manager.init_app(app) # Add this line
login_manager.login_view = 'login'

db.app = app
db.init_app(app)
migrate = Migrate(app, db)

bcrypt = Bcrypt(app)
app.config['bcrypt'] = bcrypt

accounts_bp = Blueprint("accounts", __name__)

app.register_blueprint(accounts_bp)
app.register_blueprint(api_route, url_prefix="/api")

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

def __init__(self, name, telNumber):
    self.name = name
    self.telNumber = telNumber


@app.template_filter('strfdate')
def _jinja2_filter_date(date, fmt=None):
    date = dateutil.parser.parse(date)
    native = date.replace(tzinfo=None)
    format='%b %d, %Y'
    return native.strftime(format) 

@app.template_filter('strftime')
def _jinja2_filter_time(time, fmt=None):
    native = time.replace(tzinfo=None)
    format='%I:%M %p'
    return native.strftime(format) 

'''
@app.template_filter('size')
def findSize(data):
    return data.count()
'''

@app.route("/suggestions", methods=["POST", "GET"])
def suggestions():
    return {"testarray":["test1","test2","test3"]}
    

'''
@app.route("/tutorial")
def tutorial():
    return render_template("tutorial.html")
'''
def send_json_email(to_email, json_content):
    msg = Message(json_content['subject'], recipients=[to_email])
    msg.body = json_content['message']
    msg.html = json_content['message']  # Use the same message as HTML (you can customize this)

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

@app.route(('/confirm/<token>'))
def confirm_email(token):
    try:
        email = confirm_token(token, app)
    except:
        link = app.config['REACT_SERVER'].rstrip('/')  # Remove any trailing slash
        return redirect(link + '/Login')
    user = User.query.filter_by(email=email).first_or_404()
    if not user.is_confirmed:
        user.is_confirmed = True
 #      user.updateTS = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
    link = app.config['REACT_SERVER'].rstrip('/')  # Remove any trailing slash
    return redirect(link + '/Login')



def save(text, filepath='suggestions.txt'):
    with open("suggestions.txt", "a") as f:
        f.write(text)        

if __name__ == "__main__":

    with app.app_context():

    #     db.drop_all()
     #   db.engine.execute('DROP TABLE IF EXISTS "ride_user" CASCADE')
     #   db.engine.execute('DROP TABLE IF EXISTS "ride__archive" CASCADE')
     #   db.engine.execute('DROP TABLE IF EXISTS "ride" CASCADE')

      #  print('Dropped tables: ride_user, ride_archive, ride')

        # Create the tables (in dependency order)
     #   Ride.__table__.create(db.engine)         # Create `ride` table first
     #   Ride_Archive.__table__.create(db.engine) # Create `ride_archive` next
      #  RideUser.__table__.create(db.engine)     # Create `ride_user` last

    #    db.session.commit()

    #     db.create_all()
    #     college1 = College(college_name="Emory University", email_pattern = "@emory.edu")
    #     college2 = College(college_name="Oxford College of Emory University", email_pattern = "@emory.edu")

    #     #location 1 location 2 location5
    #     db.session.commit()

        port = int(os.environ.get("PORT",5000))
        if (app.config ['ENVIRONMENT'] == 'dev'):
            app.run(debug=True)
        else:
            app.run(host="0.0.0.0",port=port)

    #    if 'liveconsole' not in gethostname():
    #        app.run(debug=True)
        