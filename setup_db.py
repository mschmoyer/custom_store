from app import app, db, Message, Cart, Order

with app.app_context():
    db.create_all()
