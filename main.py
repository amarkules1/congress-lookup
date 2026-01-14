from flask import Flask, request, redirect
import psycopg2
import psycopg2.extras
from flask_cors import CORS
import logging
from dotenv import load_dotenv, find_dotenv
import sqlalchemy
import os
import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype

# create console logger and file logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler1 = logging.StreamHandler()
handler1.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler1)
handler2 = logging.FileHandler('congress-lookup-dashboard.txt')
handler2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler2)


app = Flask(__name__, static_folder='congress-lookup-frontend/dist', static_url_path='')
CORS(app)

load_dotenv()
db_conn_string = os.getenv("DATABASE_CONN_STRING")
db_conn = psycopg2.connect(db_conn_string)

_ = load_dotenv(find_dotenv())


@app.route('/')
def hello():
    return redirect("/index.html", code=302)
