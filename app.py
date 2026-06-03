from flask import Flask, redirect, render_template
import mysql.connector
from datetime import datetime

# Conexión a MySQL 
mb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="helpesk",
)
mc = mb.cursor(dictionary=True)
app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True)
