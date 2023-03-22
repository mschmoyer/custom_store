from app import app, db, Message, Cart

with app.app_context():
    db.create_all()
