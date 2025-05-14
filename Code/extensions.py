from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

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