from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  
        gender = request.form['gender']
        religion = request.form['religion']
        race = request.form['race']
        date_of_birth = request.form['date_of_birth']
        
        # preverjanje, ali so vsi podatki vneseni
        if not username or not email or not password or not gender or not religion or not race or not date_of_birth:
            flash('Vsa polja so obvezna!', 'danger')
            return render_template('register.html')
        
        # preverjanje, ali se gesli ujemata
        if password != confirm_password:
            flash('Gesli se ne ujemata!', 'danger')
            return render_template('register.html')
        
        db = get_db()
        # preverjanje, ali uporabnik že obstaja
        cursor = db.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Uporabnik s tem e-poštnim naslovom že obstaja!', 'danger')
            return render_template('register.html')
        
        # ustvarjanje novega uporabnika
        hashed_password = generate_password_hash(password)
        try:
            db.execute('INSERT INTO users (username, email, password, gender, religion, race, date_of_birth, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                      (username, email, hashed_password, gender, religion, race, date_of_birth, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            flash('Registracija uspešna! Zdaj se lahko prijavite.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Napaka pri registraciji: {str(e)}. Poskusite znova.', 'danger')
            print(f"Database error: {str(e)}")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']  
        password = request.form['password']
        
        db = get_db()
        # preverimo, če je vnos e-poštni naslov ali uporabniško ime
        cursor = db.execute('SELECT * FROM users WHERE email = ? OR username = ?', (login_id, login_id))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], password):
            flash('Napačen e-poštni naslov/uporabniško ime ali geslo!', 'danger')
            return render_template('login.html')
        
        # Uspešna prijava
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f'Dobrodošli, {user["username"]}!', 'success')
        return redirect(url_for('home'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Uspešno ste se odjavili!', 'success')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        flash('Za dostop do profila se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    return render_template('profile.html', user=user)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Za izbris računa se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    try:
        # First delete user's event registrations
        db.execute('DELETE FROM registrations WHERE user_id = ?', (user_id,))
        
        # Check if user is an organizer of any events
        cursor = db.execute('SELECT COUNT(*) as count FROM events WHERE organizer_id = ?', (user_id,))
        event_count = cursor.fetchone()['count']
        
        if event_count > 0:
            flash('Ne morete izbrisati računa, ker ste organizator dogodkov!', 'danger')
            return redirect(url_for('profile'))
        
        # Delete the user
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        
        # Clear session
        session.pop('user_id', None)
        session.pop('username', None)
        
        flash('Vaš račun je bil uspešno izbrisan!', 'success')
        return redirect(url_for('home'))
    
    except Exception as e:
        db.rollback()
        flash(f'Napaka pri brisanju računa: {str(e)}', 'danger')
        return redirect(url_for('profile'))

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
        gender TEXT NOT NULL,
        religion TEXT NOT NULL,
        race TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
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
        
@app.route('/reset_db')
def reset_db():
    """Admin route to reset the database - use with caution!"""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    create_schema_file()
    init_db()
    flash('Database reset successfully!', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    create_schema_file()
    app.run(debug=True)
