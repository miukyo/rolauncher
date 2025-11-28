import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet
import os
import platform
import hashlib
import base64


def generate_machine_fingerprint():
    os_info = platform.platform()
    node_name = platform.node()
    processor_info = platform.processor()

    unique_string = os_info + node_name + processor_info
    machine_id = hashlib.sha256(unique_string.encode()).digest()

    return base64.urlsafe_b64encode(machine_id)


def encrypt_data(data: str) -> str:
    key = generate_machine_fingerprint()
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(data: str) -> str:
    key = generate_machine_fingerprint()
    fernet = Fernet(key)
    return fernet.decrypt(data.encode()).decode()


def get_database_path():
    local_app_data = Path(os.getenv('LOCALAPPDATA'))
    db_path = local_app_data / 'RoLauncher' / 'user_data.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def initialize_database():
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            cookie TEXT NOT NULL,
            last_account INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


def set_last_account(account_id):
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE user_info SET last_account = 0')

        cursor.execute(
            'UPDATE user_info SET last_account = 1 WHERE id = ?', (account_id,))

        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()


def get_last_account():
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, name, display_name, cookie FROM user_info WHERE last_account = 1')
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                'id': result[0],
                'name': result[1],
                'display_name': result[2],
                'cookie': decrypt_data(result[3])
            }
        else:
            return None
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()
        return None


def save_user_info(user_info, cookie):
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        encrypted_cookie = encrypt_data(cookie)

        cursor.execute('''
            INSERT OR REPLACE INTO user_info (id, name, display_name, cookie)
            VALUES (?, ?, ?, ?)
        ''', (user_info['id'], user_info['name'], user_info['displayName'], encrypted_cookie))

        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        encrypted_cookie = encrypt_data(cookie)
        cursor.execute('''
            INSERT OR REPLACE INTO user_info (id, name, display_name, cookie)
            VALUES (?, ?, ?, ?)
        ''', (user_info['id'], user_info['name'], user_info['displayName'], encrypted_cookie))

        conn.commit()
        conn.close()


def purge_database():
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_info')

        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()


def get_all_accounts():
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, display_name FROM user_info')
        accounts = cursor.fetchall()

        account_list = [
            {
                'id': account[0],
                'name': account[1],
                'display_name': account[2]
            }
            for account in accounts
        ]

        conn.close()
        return account_list
    except (sqlite3.OperationalError, sqlite3.DatabaseError):

        initialize_database()
        return []


def get_account(account_id):
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, name, display_name, cookie FROM user_info WHERE id = ?', (account_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                'id': result[0],
                'name': result[1],
                'display_name': result[2],
                'cookie': decrypt_data(result[3])
            }
        else:
            raise ValueError("Account not found")
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()
        raise ValueError("Account not found - database was reinitialized")


def delete_account(account_id):
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM user_info WHERE id = ?', (account_id,))

        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        initialize_database()


# def switch_account(account_id):
#     try:
#         db_path = get_database_path()
#         conn = sqlite3.connect(db_path)
#         cursor = conn.cursor()

#         cursor.execute(
#             'SELECT cookie FROM user_info WHERE id = ?', (account_id,))
#         result = cursor.fetchone()

#         conn.close()

#         if result:
#             encrypted_cookie = result[0]
#             set_last_account(account_id)  # Mark this account as the last used
#             return decrypt_data(encrypted_cookie)
#         else:
#             raise ValueError("Account not found")
#     except (sqlite3.OperationalError, sqlite3.DatabaseError):

#         initialize_database()
#         raise ValueError("Account not found - database was reinitialized")
