from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Adolf'

DATABASE = 'eventlink.db'

# Define common choices for dropdown menus
RELIGIONS = ['Katoliška', 'Pravoslavna', 'Protestantska', 'Islam', 'Judovska', 'Hinduizem', 'Budizem', 'Ateizem', 'Drugo']
RACES = ['Belci', 'Črnci', 'Azijci', 'Latinoameričani', 'Arabci', 'Drugo']
AGE_GROUPS = ['all', 'adults', 'minors']

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
            return render_template('register.html', religions=RELIGIONS, races=RACES)
        
        # preverjanje, ali se gesli ujemata
        if password != confirm_password:
            flash('Gesli se ne ujemata!', 'danger')
            return render_template('register.html', religions=RELIGIONS, races=RACES)
        
        db = get_db()
        # preverjanje, ali uporabnik že obstaja
        cursor = db.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Uporabnik s tem e-poštnim naslovom že obstaja!', 'danger')
            return render_template('register.html', religions=RELIGIONS, races=RACES)
        
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
    
    return render_template('register.html', religions=RELIGIONS, races=RACES)

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

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Za urejanje profila se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    if request.method == 'POST':
        # data
        username = request.form['username']
        email = request.form['email']
        gender = request.form['gender']
        religion = request.form['religion']
        race = request.form['race']
        date_of_birth = request.form['date_of_birth']
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # preveri ali so zapolnjeni
        if not username or not email or not gender or not religion or not race or not date_of_birth:
            flash('Vsa polja so obvezna!', 'danger')
            return redirect(url_for('edit_profile'))
        
        # pridobivanje uporabnika
        cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        # preveri mail
        if email != user['email']:
            cursor = db.execute('SELECT * FROM users WHERE email = ? AND id != ?', (email, user_id))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('E-poštni naslov je že v uporabi!', 'danger')
                return redirect(url_for('edit_profile'))
        
        try:
            # ce zelis zamenjati geslo
            if current_password and new_password:
                # Verify current password
                if not check_password_hash(user['password'], current_password):
                    flash('Trenutno geslo ni pravilno!', 'danger')
                    return redirect(url_for('edit_profile'))
                
                # prevera gesla
                if new_password != confirm_password:
                    flash('Novi gesli se ne ujemata!', 'danger')
                    return redirect(url_for('edit_profile'))
                
                # posodobi uporabnika z geslom
                hashed_password = generate_password_hash(new_password)
                db.execute('''
                    UPDATE users 
                    SET username = ?, email = ?, gender = ?, religion = ?, race = ?, 
                        date_of_birth = ?, password = ?
                    WHERE id = ?
                ''', (username, email, gender, religion, race, date_of_birth, hashed_password, user_id))
            else:
                # posodobi uporabnika brez gesla
                db.execute('''
                    UPDATE users 
                    SET username = ?, email = ?, gender = ?, religion = ?, race = ?, date_of_birth = ?
                    WHERE id = ?
                ''', (username, email, gender, religion, race, date_of_birth, user_id))
            
            db.commit()
            
            # posodobi ce se ime zamenja
            if username != session['username']:
                session['username'] = username
                
            flash('Profil uspešno posodobljen!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.rollback()
            flash(f'Napaka pri posodabljanju profila: {str(e)}', 'danger')
            return redirect(url_for('edit_profile'))
    
    # GET request - show form with current data
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    return render_template('edit_profile.html', user=user, religions=RELIGIONS, races=RACES)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session:
        flash('Za ustvarjanje dogodka se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Pridobivanje podatkov iz obrazca
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        target_age_group = request.form.get('target_age_group', 'all')
        organizer_id = session['user_id']
        
        # Get target groups data
        target_religions = request.form.getlist('target_religions')
        target_races = request.form.getlist('target_races')
        
        # Preveri, če so vsi potrebni podatki vneseni
        if not title or not description or not date or not time or not location:
            flash('Vsa polja so obvezna!', 'danger')
            return render_template('create_event.html', religions=RELIGIONS, races=RACES)
        
        # Združevanje datuma in časa v eno vrednost
        event_datetime = f"{date} {time}"
        
        # Validacija datuma (mora biti v prihodnosti)
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
            if event_date < datetime.now().date():
                flash('Datum dogodka mora biti v prihodnosti!', 'danger')
                return render_template('create_event.html', religions=RELIGIONS, races=RACES)
        except ValueError:
            flash('Neveljaven format datuma!', 'danger')
            return render_template('create_event.html', religions=RELIGIONS, races=RACES)
        
        db = get_db()
        try:
            # Vstavi nov dogodek v bazo
            cursor = db.execute(
                'INSERT INTO events (title, description, date, location, organizer_id, target_age_group, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (title, description, event_datetime, location, organizer_id, target_age_group, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            event_id = cursor.lastrowid
            
            # Vstavi ciljne skupine za religijo
            for religion in target_religions:
                db.execute(
                    'INSERT INTO event_target_groups (event_id, group_type, group_value) VALUES (?, ?, ?)',
                    (event_id, 'religion', religion)
                )
            
            # Vstavi ciljne skupine za rase
            for race in target_races:
                db.execute(
                    'INSERT INTO event_target_groups (event_id, group_type, group_value) VALUES (?, ?, ?)',
                    (event_id, 'race', race)
                )
            
            db.commit()
            flash('Dogodek uspešno ustvarjen!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            flash(f'Napaka pri ustvarjanju dogodka: {str(e)}', 'danger')
            return render_template('create_event.html', religions=RELIGIONS, races=RACES)
    
    # GET request - prikaži obrazec
    return render_template('create_event.html', religions=RELIGIONS, races=RACES)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    if not event_id:
        flash('Dogodek ni bil najden!', 'danger')
        return redirect(url_for('home'))
    
    db = get_db()
    
    # Get event details
    cursor = db.execute('SELECT e.*, u.username as organizer_name FROM events e JOIN users u ON e.organizer_id = u.id WHERE e.id = ?', (event_id,))
    event = cursor.fetchone()
    
    if not event:
        flash('Dogodek ni bil najden!', 'danger')
        return redirect(url_for('home'))
    
    # Get target groups for the event
    cursor = db.execute('SELECT group_type, group_value FROM event_target_groups WHERE event_id = ?', (event_id,))
    target_groups = cursor.fetchall()
    
    # Process target groups
    target_religions = []
    target_races = []
    for group in target_groups:
        if group['group_type'] == 'religion':
            target_religions.append(group['group_value'])
        elif group['group_type'] == 'race':
            target_races.append(group['group_value'])
    
    # Get number of registrations
    cursor = db.execute('SELECT COUNT(*) as count FROM registrations WHERE event_id = ?', (event_id,))
    registrations_count = cursor.fetchone()['count']
    
    # Check if current user is registered
    is_registered = False
    if 'user_id' in session:
        cursor = db.execute('SELECT * FROM registrations WHERE user_id = ? AND event_id = ?', 
                           (session['user_id'], event_id))
        is_registered = cursor.fetchone() is not None
    
    return render_template('event_detail.html', 
                          event=event, 
                          target_religions=target_religions,
                          target_races=target_races,
                          registrations_count=registrations_count,
                          is_registered=is_registered)

@app.route('/event/<int:event_id>/register', methods=['POST'])
def register_for_event(event_id):
    if 'user_id' not in session:
        flash('Za prijavo na dogodek se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    # Check if event exists
    cursor = db.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    if not event:
        flash('Dogodek ne obstaja!', 'danger')
        return redirect(url_for('home'))
    
    # Check if user is already registered
    cursor = db.execute('SELECT * FROM registrations WHERE user_id = ? AND event_id = ?', 
                       (user_id, event_id))
    if cursor.fetchone():
        flash('Že ste prijavljeni na ta dogodek!', 'warning')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Check user eligibility based on target groups
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    # Check age group
    if event['target_age_group'] != 'all':
        user_birth_date = datetime.strptime(user['date_of_birth'], '%Y-%m-%d').date()
        user_age = (datetime.now().date() - user_birth_date).days // 365
        
        if (event['target_age_group'] == 'adults' and user_age < 18) or \
           (event['target_age_group'] == 'minors' and user_age >= 18):
            flash('Ta dogodek ni namenjen vaši starostni skupini!', 'danger')
            return redirect(url_for('event_detail', event_id=event_id))
         
    
    # Register the user
    try:
        db.execute('INSERT INTO registrations (user_id, event_id, registered_at) VALUES (?, ?, ?)',
                  (user_id, event_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        flash('Uspešno ste se prijavili na dogodek!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Napaka pri prijavi na dogodek: {str(e)}', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/event/<int:event_id>/unregister', methods=['POST'])
def unregister_from_event(event_id):
    if 'user_id' not in session:
        flash('Za odjavo od dogodka se morate prijaviti!', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    try:
        db.execute('DELETE FROM registrations WHERE user_id = ? AND event_id = ?', (user_id, event_id))
        db.commit()
        flash('Uspešno ste se odjavili od dogodka!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Napaka pri odjavi od dogodka: {str(e)}', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))

# shema baze
def create_schema_file():
    with open('schema.sql', 'w') as f:
        f.write('''
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS registrations;
DROP TABLE IF EXISTS event_target_groups;

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
    target_age_group TEXT DEFAULT 'all',
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

CREATE TABLE event_target_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    group_type TEXT NOT NULL,  -- 'religion' or 'race'
    group_value TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events (id)
);
        ''')
        
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