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

from multiprocessing import Process

from gradio_interface import run_gradio_interface



# gradio_interface = gr.Interface(fn=run_gradio_interface, inputs="text", outputs="text")

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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            background-image: url('/static/images/background.jpeg'); 
            background-size: cover; 
            background-position: center; 
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh; 
            margin: 40px;
        }}
        p {{
            font-size: 48px; 
            margin: 20px 0; 
        }}
        .pretty-button {{
            background-color: #4CAF50; 
            border: none;
            color: white; 
            padding: 15px 60px; 
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 28px; 
            margin: 20px 5px; 
            cursor: pointer;
            border-radius: 8px; 
            transition-duration: 0.4s; 
        }}

        .pretty-button:hover {{
            background-color: white; 
            color: black; 
        }}
    </style>
    </head>
    <body>
        <p>Welcome to Our Innovative Learning Platform </p>
        <a href='/login'><button class='pretty-button'>Login</button></a>
    </body>
    </html>
    """
    


@app.route("/protected_area")
@login_is_required
def protected_area():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            background-image: url('/static/images/background.jpeg'); 
            background-size: cover; 
            background-position: center; 
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh; 
            margin: 40px;
        }}
        p {{
            font-size: 36px; 
            margin: 20px 0; 
        }}
        .pretty-button {{
            background-color: #4CAF50; 
            border: none;
            color: white; 
            padding: 15px 60px; 
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 28px;
            margin: 20px 5px; 
            cursor: pointer;
            border-radius: 8px; 
            transition-duration: 0.4s; 
        }}

        .pretty-button:hover {{
            background-color: white; 
            color: black; 
        }}
    </style>
    </head>
    <body>
        <p>Welcome {session['name']}!</p>
        <a href='/gradioThread'><button class='pretty-button'>Gradio</button></a>
        <a href='/logout'><button class='pretty-button'>Logout</button></a>
        <a href='/register'><button class='pretty-button'>Register</button></a>
    </body>
    </html>
    """


# @app.route('/gradio', methods=['GET'])
# def gradio_app():
#     run_gradio_interface().launch(server_name="0.0.0.0", server_port=7860, inbrowser=False, share=False)

def run_gradio():
    gradio_app = run_gradio_interface()
    gradio_app.launch(server_name='0.0.0.0', server_port=7860, inbrowser=False)



@app.route('/gradioThread')
def home():
    return render_template_string('''
        <h1>Flask and Gradio Integration</h1>
        <iframe src="http://localhost:7860" width="100%" height="100%"></iframe>
        <br/> <a href='/logout'><button>Logout</button></a>
        <a href='/protected_area'><button>Home Page</button></a>
        
    ''')



# threading.Thread(target=gradio_app, daemon=True).start()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        if not email.endswith('@gmail.com'):
            return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    height: 100vh; 
                    display: flex;
                    flex-direction: column;
                    justify-content: center; 
                    align-items: center; 
                    text-align: center;
                    background-image: url('/static/images/background.jpeg'); 
                    background-size: cover; 
                    background-position: center; 
                }
                p {
                    color: #333; 
                    font-size = 48px;
                    margin: 10px 0;
                }
                a {
                    color: #007bff; 
                    text-decoration: none; 
                    margin: 10px 0; 
                }
                a:hover {
                    text-decoration: underline;
                }
                
                .pretty-button {
            background-color: #4CAF50; 
            border: none;
            color: white; 
            padding: 15px 60px; 
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 28px; 
            margin: 20px 5px; 
            cursor: pointer;
            border-radius: 8px; 
            transition-duration: 0.4s; 
        }

        .pretty-button:hover {
            background-color: white; 
            color: black; 
        }
            </style>
        </head>
        <body>
            <p>Only Gmail addresses are accepted. Please provide a valid Gmail address.</p>
            <a href="/register">Try again</a>
        </body>
        </html>
    ''')
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # User with this email already exists
            return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    height: 100vh; 
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center; 
                    text-align: center;
                    background-image: url('/static/images/background.jpeg'); 
                    background-size: cover;
                    background-position: center; 
                }
                p {
                    color: #333; 
                    font-size = 48px;
                    margin: 10px 0; 
                }
                a {
                    color: #007bff; 
                    text-decoration: none; 
                    margin: 10px 0; 
                }
                a:hover {
                    text-decoration: underline; 
                }
                
                .pretty-button {
            background-color: #4CAF50; 
            border: none;
            color: white; 
            padding: 15px 60px; 
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 28px;
            margin: 20px 5px; 
            cursor: pointer;
            border-radius: 8px; 
            transition-duration: 0.4s; 
        }

        .pretty-button:hover {
            background-color: white; 
            color: black; 
        }
            </style>
        </head>
        <body>
            <p>This email is already registered. Please use a different email.</p>
            <a href="/register">Try again</a>
            <a href='/gradioThread'><button class='pretty-button'>Gradio</button></a>
        </body>
        </html>
    ''')

        # Save to database
        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('profile', user_id=new_user.id))

    return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif; 
                    padding: 20px; 
                    text-align: center;
                    background-image: url('/static/images/background.jpeg'); 
                    background-size: cover; 
                    background-position: center; 
                }
                form {
                    background-color: #f2f2f2; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); 
                    margin-bottom: 20px; 
                }
                input[type=text], input[type=email] {
                    width: 50%; 
                    padding: 12px 20px; 
                    margin: 8px 0; 
                    display: inline-block; 
                    border: 1px solid #ccc; 
                    border-radius: 4px; 
                    box-sizing: border-box; 
                }
                input[type=submit] {
                    width: 50%;
                    background-color: #4CAF50; 
                    color: white; 
                    padding: 14px 20px; 
                    margin: 8px 0; 
                    border: none;
                    border-radius: 4px; 
                    cursor: pointer; 
                }
                input[type=submit]:hover {
                    background-color: #45a049; 
                }
                .pretty-button {
            background-color: #4CAF50; 
            border: none;
            color: white; 
            padding: 15px 60px; 
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 28px; 
            margin: 20px 5px; 
            cursor: pointer;
            border-radius: 8px; 
            transition-duration: 0.4s; 
        }

        .pretty-button:hover {
            background-color: white; 
            color: black; 
        }
                
            </style>
        </head>
        <body>
            <form method="post">
                Username: <input type="text" name="username"><br>
                Email: <input type="email" name="email"><br>
                <input type="submit" value="Register">
            </form>
            <br/> <a href='/gradioThread'><button class='pretty-button'>Gradio</button></a>
        </body>
        </html>
    ''')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    return render_template_string('''
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    height: 100vh; 
                    display: flex;
                    flex-direction: column;
                    justify-content: center; 
                    align-items: center; 
                    text-align: center;
                    background-image: url('/static/images/background.jpeg'); 
                    background-size: cover; 
                    background-position: center; 
                }
                h1 {
                    color: #fff;
                    text-shadow: 2px 2px 4px #000; 
                }
                p {
                    color: #fff; 
                    text-shadow: 1px 1px 3px #000; 
                }
                .pretty-button {
                    background-color: #4CAF50; 
                    color: white; 
                    padding: 10px 20px; 
                    border: none;
                    border-radius: 5px; 
                    font-size: 16px; 
                    cursor: pointer; 
                    margin-top: 15px; 
                }
                .pretty-button:hover {
                    background-color: #45a049; 
                }
                a {
                    text-decoration: none; 
                }
            </style>
        </head>
        <body>
            <h1>User Profile</h1>
            <p>Username: {{ user.username }}</p>
            <p>Email: {{ user.email }}</p>
            <br/> <a href='/gradioThread'><button class='pretty-button'>Gradio</button></a>
        </body>
        </html>
    ''', user=user)

if __name__ == "__main__":
    gradio_process = Process(target=run_gradio)
    gradio_process.start()
    app.run()