from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# =========================
# Admin Model
# =========================
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================
# Staff Model
# =========================
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================
# Room Model
# =========================
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(10), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    occupied = db.Column(db.Integer, default=0)
    students = db.relationship('Student', back_populates='room')


# =========================
# Student Model
# =========================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship('Room', back_populates='students')

    last_active = db.Column(db.DateTime, nullable=True)
    last_active_ip = db.Column(db.String(45), nullable=True)
    is_assigned = db.Column(db.Boolean, default=False)

    # ✅ Relationships (one-directional with cascade delete)
    complaints = db.relationship('Complaint', backref='student', cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref='student', cascade='all, delete-orphan')
    gate_passes = db.relationship('GatePass', backref='student', cascade='all, delete-orphan')
    fees = db.relationship('Fees', backref='student', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='student', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================
# Product Model
# =========================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    min_quantity = db.Column(db.Integer, default=1)


# =========================
# Complaint Model
# =========================
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Cart Model
# =========================
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # ✅ Only product relationship defined here
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))


# =========================
# GatePass Model
# =========================
class GatePass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    reason = db.Column(db.String(200), nullable=False)
    leave_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Fees Model
# =========================
class Fees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount_due = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='Pending')

    @property
    def balance(self):
        return self.amount_due - self.amount_paid


# =========================
# Order Model
# =========================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Only product relationship defined here
    product = db.relationship('Product', backref='orders')
