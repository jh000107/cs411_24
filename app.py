import os
import pathlib

import requests
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from flask import Flask, render_template_string

from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


import gradio as gr
import threading

def hello_world(input):
  return ("hey " + input + " take care.")

gradio_interface = gr.Interface(fn=hello_world, inputs="text", outputs="text")

app = Flask("Google Login App")
app.secret_key = "CodeSpecialist.com"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "108520371819-facfflvpsst1if98oj3sk1o2sch6tqgn.apps.googleusercontent.com"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Add other profile fields as needed

    def __repr__(self):
        return '<User %r>' % self.username

with app.app_context():
    db.create_all()

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    return "Hello World <a href='/login'><button>Login</button></a>"


@app.route("/protected_area")
@login_is_required
def protected_area():
    return f"Hello {session['name']}! <br/> <a href='/gradioThread'><button>Gradio</button></a> <br/> <a href='/logout'><button>Logout</button></a> <br/> <a href='/register'><button>Register</button></a>"

@app.route('/gradio', methods=['GET'])
def gradio_app():
    gradio_interface.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)

@app.route('/gradioThread')
def home():
    return render_template_string('''
        <h1>Flask and Gradio Integration</h1>
        <iframe src="http://localhost:7860" width="100%" height="500"></iframe>
        <br/> <a href='/logout'><button>Logout</button></a>
    ''')

threading.Thread(target=gradio_app, daemon=True).start()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        if not email.endswith('@gmail.com'):
            return render_template_string('''
                <p>Only Gmail addresses are accepted. Please provide a valid Gmail address.</p>
                <a href="/register">Try again</a>
            ''')
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # User with this email already exists
            return render_template_string('''
                <p>This email is already registered. Please use a different email.</p>
                <a href="/register">Try again</a>
                <p> Use Gradio </p>
                <br/> <a href='/gradioThread'><button>Gradio</button></a>

            ''')

        # Save to database
        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('profile', user_id=new_user.id))

    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Email: <input type="email" name="email"><br>
            <!-- Add other fields here -->
            <input type="submit" value="Register">
        </form>
        <br/> <a href='/gradioThread'><button>Gradio</button></a>
    ''')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template_string('''
        <h1>User Profile</h1>
        <p>Username: {{ user.username }}</p>
        <p>Email: {{ user.email }}</p>
        <!-- Display other fields -->
        <br/> <a href='/gradioThread'><button>Gradio</button></a>
    ''', user=user)

if __name__ == "__main__":
    app.run()