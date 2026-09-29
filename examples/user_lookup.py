import sqlite3
import hashlib

SECRET_KEY = "changeme123"

def get_user(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor() 
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    row = cursor.fetchone() 
    return row["email"] 

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest() 

def average(values):
    return sum(values)/ len(values)