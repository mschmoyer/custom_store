# models.py

from datetime import datetime
from database import db

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'product_id': self.product_id,
            'quantity': self.quantity
        }

class Order(db.Model):
    id = db.Column(db.String, primary_key=True)
    product_ids = db.Column(db.String)
    shipping_info = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shipped = db.Column(db.Boolean)

    def __init__(self, id, product_ids, shipping_info, shipped):
        self.id = id
        self.product_ids = product_ids
        self.shipping_info = shipping_info
        self.shipped = False
