from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()


import smtplib

class CustomMail(Mail):
    def connect(self):
        connection = super().connect()
        if isinstance(connection, smtplib.SMTP):
            connection.local_hostname = 'localhost'
            # Ajouter l'encodage en UTF-8
            connection.set_debuglevel(1)
            connection.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection.sock.setsockopt(socket.IPPROTO_TCP, socket.SO_RCVBUF, 0)
        return connection


mail = CustomMail()


@event.listens_for(Engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    # S'applique uniquement pour SQLite
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        try:
            cursor.execute("PRAGMA busy_timeout = 5000;")  # 5s
        except Exception:
            pass
        cursor.close()