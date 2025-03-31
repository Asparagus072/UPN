from flask import Flask, request, g, render_template
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'Adolf'

DATABASE = 'eventlink.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # da lahko dostopamo do stolpcev po imenih
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# inicializacija baze
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# osnovna stran
@app.route('/')
def home():
    db = get_db()
    cursor = db.execute('SELECT * FROM events ORDER BY date LIMIT 3')
    events = cursor.fetchall()
    return render_template('home.html', events=events)

@app.route('/register, methods=['GET, 'POST']')

# shema baze
def create_schema_file():
    schema = '''
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS events;
    DROP TABLE IF EXISTS registrations;
    
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        date TEXT NOT NULL,
        location TEXT NOT NULL,
        organizer_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (organizer_id) REFERENCES users (id)
    );
    
    CREATE TABLE registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        registered_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (event_id) REFERENCES events (id)
    );
    '''
    with open('schema.sql', 'w') as f:
        f.write(schema)
        
    if not os.path.exists(DATABASE):
        init_db()

if __name__ == '__main__':
    create_schema_file()
    app.run(debug=True)