import sqlite3

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name

    def create_connection(self):
        # conn = None
        # try:
        conn = sqlite3.connect(self.db_name)
        self.create_tables(conn)

        # except sqlite3.Error as e:
        #     print(e)

        return conn

    def close_connection(self, conn):
        conn.close()

    def create_tables(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS categories
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS records
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            category_id INTEGER REFERENCES categories(id),
                            elapsed_time INTEGER NOT NULL,
                            timestamp TEXT NOT NULL,
                            FOREIGN KEY (category_id) REFERENCES categories (id)
                            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                        (id INTEGER PRIMARY KEY, active_category_id INTEGER)''')
            cursor.execute("INSERT OR IGNORE INTO settings (id, active_category_id) VALUES (1, NULL)")

        except sqlite3.Error as e:
            print(e)
