
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
        