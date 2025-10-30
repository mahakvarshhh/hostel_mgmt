import os
from flask import Flask
from app import db
from models import Student, Staff, Admin, Product, Room, Complaint, Cart, GatePass

# ----------------------------
# Flask App Configuration
# ----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'

# Ensure absolute path for database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'hostel_management.db')

# Create instance folder if it doesn't exist
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect db to app
db.init_app(app)

# ----------------------------
# Database Initialization
# ----------------------------
def initialize_database():
    """Initializes and populates the database with sample data."""

    # Remove existing database file if it exists
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Existing database file removed.")
        except OSError as e:
            print(f"Error removing database file: {e}")
            return

    with app.app_context():
        # Drop and create tables
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # ----------------------------
        # Sample Admin
        # ----------------------------
        admin = Admin(username='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
        print("Sample admin user created.")

        # ----------------------------
        # Sample Staff
        # ----------------------------
        staff1 = Staff(name='Jane Doe', email='jane.doe@example.com', department='Administration')
        staff1.set_password('staffpass')
        db.session.add(staff1)
        print("Sample staff user created.")

        # ----------------------------
        # Sample Students
        # ----------------------------
        student1 = Student(roll='101', name='Alice Smith', email='alice.smith@example.com')
        student1.set_password('studentpass')
        db.session.add(student1)

        student2 = Student(roll='102', name='Bob Johnson', email='bob.johnson@example.com')
        student2.set_password('studentpass')
        db.session.add(student2)
        print("Sample students created.")

        # ----------------------------
        # Sample Rooms
        # ----------------------------
        rooms = [
            Room(room_no='A-101', capacity=2, occupied=0),
            Room(room_no='A-102', capacity=3, occupied=0),
            Room(room_no='A-103', capacity=2, occupied=0),
            Room(room_no='A-104', capacity=2, occupied=0),
            Room(room_no='A-105', capacity=3, occupied=0),
            Room(room_no='B-101', capacity=2, occupied=0),
            Room(room_no='B-102', capacity=2, occupied=0),
            Room(room_no='B-103', capacity=3, occupied=0),
            Room(room_no='B-104', capacity=2, occupied=0),
            Room(room_no='B-105', capacity=3, occupied=0),
            Room(room_no='C-101', capacity=2, occupied=0),
            Room(room_no='C-102', capacity=2, occupied=0),
        ]
        db.session.add_all(rooms)

        # Assign student1 to room A-101
        student1.room = rooms[0]
        student1.is_assigned = True
        rooms[0].occupied = 1

        # ----------------------------
        # Sample Products
        # ----------------------------
               # ----------------------------
        # Sample Products
        # ----------------------------
        products = [
            Product(name='Notebook', description='Lined notebook for class notes', price=60, stock=50, min_quantity=2),
            Product(name='Pen Set', description='Set of blue and black pens', price=30, stock=25, min_quantity=5),
            Product(name='Eraser', description='Rubber eraser', price=50, stock=100, min_quantity=1),
            Product(name='Pencil', description='HB pencil', price=25, stock=100, min_quantity=1),
            Product(name='Marker', description='Permanent marker', price=100, stock=40, min_quantity=1),
            Product(name='Ruler', description='30cm plastic ruler', price=50, stock=50, min_quantity=2),
            Product(name='Sharpener', description='Pencil sharpener', price=75, stock=60, min_quantity=0),
            Product(name='Glue Stick', description='20g glue stick', price=20, stock=30, min_quantity=5),
            Product(name='Highlighter', description='Yellow highlighter pen', price=50, stock=50),
            Product(name='Sketch Book', description='A4 sheets (50)', price=250, stock=20, min_quantity=1),
        ]
        db.session.add_all(products)
        print("Sample products (15-20) created.")

        # Commit all changes
        db.session.commit()
        print("Database populated with sample data successfully.")


# ----------------------------
# Run Initialization
# ----------------------------
if __name__ == '__main__':
    initialize_database()
