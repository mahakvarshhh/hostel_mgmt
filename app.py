import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from extensions import db
from models import Student, Staff, Admin, Product, Room, Complaint, Cart, GatePass,Fees,Room,Order
import calendar
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'hostel_management.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Now, link the db instance to the app.
db.init_app(app)


def create_initial_users():
    """
    Creates default admin, staff, and student users if they don't exist.
    This function should be called inside the app context.
    """
    print("Checking for initial users...")
    
    # Check if admin user exists
    
    if not Admin.query.filter_by(username='admin').first():
        print("Admin user not found. Creating default users...")
        
        # Create a default admin user
        admin = Admin(username='admin')
        admin.set_password('admin')
        db.session.add(admin)

        # Create a default staff user
        staff = Staff(name='Default Staff', email='staff@example.com', department='General')
        staff.set_password('password')
        db.session.add(staff)

        # Create a default student user
        student = Student(roll='12345', name='Default Student', email='student@example.com')
        student.set_password('password')
        db.session.add(student)
        
        db.session.commit()
        print("Default users created successfully.")
        print("---")
        print("Login Credentials:")
        print("Admin: Username='admin', Password='admin'")
        print("Staff: Email='staff@example.com', Password='password'")
        print("Student: Roll='12345', Password='password'")
        print("---")
    else:
        print("Initial users already exist. Skipping creation.")



@app.route('/')
def index():
    return render_template('login.html')

@app.before_request
def update_last_active():
    # Only update for logged-in students
    if 'logged_in' in session and session.get('role') == 'student':
        student_id = session.get('user_id')
        student = Student.query.get(student_id)
        if student:
            # Store local IST time directly
            ist = ZoneInfo("Asia/Kolkata")
            student.last_active = datetime.now(ist)  
            student.last_active_ip = request.remote_addr
            db.session.commit()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import Admin  # Make sure this imports your Admin model
from extensions import db
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']

        print(f"Attempting login for role: {role} with username/roll/email: {username}")

        user = None
        if role == 'admin':
            user = Admin.query.filter_by(username=username).first()
        elif role == 'staff':
            user = Staff.query.filter_by(email=username).first()
        elif role == 'student':
            user = Student.query.filter_by(roll=username).first()

        if user:
            # Use appropriate attribute for username/email/roll in logs
            user_display = getattr(user, 'username', None) or getattr(user, 'email', None) or getattr(user, 'roll', None)
            print("User found:", user_display)

            if user.check_password(password):
                # ✅ Set session keys
                session['user_id'] = user.id
                session['role'] = role
                session['logged_in'] = True

                flash('Login successful!', 'success')

                # ✅ Redirect based on role
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'staff':
                    return redirect(url_for('staff_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                flash('Incorrect password', 'danger')
                print("Password check failed")
        else:
            flash('User not found', 'danger')
            print("User not found")

        return redirect(url_for('login'))

    return render_template('login.html')




@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Admin Routes ---
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    students = Student.query.all()
    staff = Staff.query.all()
    rooms = Room.query.all()
    products = Product.query.all()
    gate_passes = GatePass.query.all()
    complaints = Complaint.query.all()

    # Define local timezone
    local_tz = ZoneInfo("Asia/Kolkata")

    # Pass datetime and local_tz to Jinja
    return render_template(
        'admin_dashboard.html',
        students=students,
        staff=staff,
        rooms=rooms,
        products=products,
        gate_passes=gate_passes,
        complaints=complaints,
        datetime=datetime,
        local_tz=local_tz
    )

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    roll = request.form.get('roll')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    existing_student = Student.query.filter_by(roll=roll).first()
    if existing_student:
        flash('Student with this roll number already exists.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_student = Student(roll=roll, name=name, email=email)
    new_student.set_password(password)

    db.session.add(new_student)
    db.session.commit()

    flash('Student added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))



@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        new_roll = request.form['roll']

        # Check if another student already has this roll
        existing = Student.query.filter_by(roll=new_roll).first()
        if existing and existing.id != student_id:
            flash(f"Roll number {new_roll} is already taken by another student.", "danger")
            return redirect(url_for('edit_student', student_id=student_id))

        student.roll = new_roll
        student.name = request.form['name']
        student.email = request.form['email']
        student.room_id = request.form.get('room_id') or None

        # ✅ Handle password update
        new_password = request.form.get('password')
        if new_password and new_password.strip() != "":
            student.set_password(new_password)  # use your model's method
 # hash password for security

        try:
            db.session.commit()
            flash('Student details updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating student: ' + str(e), 'danger')
        
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_student.html', student=student)

@app.route('/staff/add_product', methods=['GET', 'POST'])
def staff_add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        min_quantity = int(request.form['min_quantity'])
        new_product = Product(name=name, price=price, min_quantity=min_quantity)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('staff_dashboard'))
    
    # For the form, pass None since it's a new product
    return render_template('edit_product.html', product=None)


@app.route('/staff/edit_product/<int:product_id>', methods=['GET', 'POST'])
def staff_edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.min_quantity = int(request.form['min_quantity'])
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('staff_dashboard'))

    return render_template('edit_product.html', product=product)
@app.route('/staff/delete_product/<int:product_id>', methods=['POST', 'GET'])
def staff_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('staff_dashboard'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/assign_room/<int:student_id>', methods=['GET', 'POST'])
def assign_room(student_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    student = Student.query.get_or_404(student_id)
    rooms = Room.query.order_by(Room.room_no).all()

    if request.method == 'POST':
        room_no = request.form.get('room_no')
        room = Room.query.filter_by(room_no=room_no).first()

        if not room or room.occupied >= room.capacity:
            flash('Selected room is full or does not exist.', 'danger')
            return redirect(url_for('assign_room', student_id=student_id))

        # Unassign old room if exists
        if student.room:
            old_room = student.room
            old_room.occupied -= 1

        # Assign new room
        student.room = room
        room.occupied += 1
        student.is_assigned = True
        db.session.commit()

        flash(f'Room {room.room_no} assigned to {student.name} successfully!', 'success')
        return redirect(url_for('assign_room', student_id=student_id))  # stay on the same page

    # Here: only True if student.room exists
    room_assigned = True if student.room else False
    return render_template('assign_room.html', student=student, rooms=rooms, room_assigned=room_assigned)

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    department = request.form.get('department')
    
    existing_staff = Staff.query.filter_by(email=email).first()
    if existing_staff:
        flash('Staff with this email already exists.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    new_staff = Staff(name=name, email=email, department=department)
    new_staff.set_password(password)
    db.session.add(new_staff)
    db.session.commit()
    
    flash('Staff member added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/edit_staff/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    # Only admin can edit
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    staff = Staff.query.get_or_404(staff_id)

    if request.method == 'POST':
        new_email = request.form['email']

        # Check if another staff already has this email
        existing = Staff.query.filter_by(email=new_email).first()
        if existing and existing.id != staff_id:
            flash(f"Email {new_email} is already used by another staff member.", "danger")
            return redirect(url_for('edit_staff', staff_id=staff_id))

        # Update staff details
        staff.name = request.form['name']
        staff.email = new_email
        staff.department = request.form['department']

        try:
            db.session.commit()
            flash('Staff member updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating staff: ' + str(e), 'danger')

        return redirect(url_for('admin_dashboard'))

    return render_template('edit_staff.html', staff=staff)

@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    
    flash('Staff member deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- Staff Routes ---
@app.route('/staff/dashboard')
def staff_dashboard():
    if 'logged_in' not in session or session['role'] != 'staff':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    products = Product.query.all()
    pending_gate_passes = GatePass.query.filter_by(status='Pending').all()  # <-- fetch pending passes
    orders = Order.query.order_by(Order.ordered_at.desc()).all()
    return render_template(
        'staff_dashboard.html', 
        products=products, 
        orders=orders,
        pending_gate_passes=pending_gate_passes  # <-- pass to template
    )


# Approve gate pass
@app.route('/approve_gate_pass/<int:gp_id>')
def approve_gate_pass(gp_id):
    gate_pass = GatePass.query.get_or_404(gp_id)
    gate_pass.status = 'Approved'
    db.session.commit()
    flash(f'Gate pass for {gate_pass.student.name} approved!', 'success')
    return redirect(url_for('staff_dashboard'))

# Reject gate pass
@app.route('/reject_gate_pass/<int:gp_id>')
def reject_gate_pass(gp_id):
    gate_pass = GatePass.query.get_or_404(gp_id)
    gate_pass.status = 'Rejected'
    db.session.commit()
    flash(f'Gate pass for {gate_pass.student.name} rejected!', 'info')
    return redirect(url_for('staff_dashboard'))



# --- Student Routes ---@app.route('/student_dashboard')@app.route('/student_dashboard')@app.route('/student_dashboard')
# --- Student Routes ---
from datetime import datetime

@app.route('/student_dashboard')
def student_dashboard():
    student_id = session.get('user_id')
    if not student_id:
        flash("You must log in first!", "danger")
        return redirect(url_for('login'))

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found!", "danger")
        session.clear()
        return redirect(url_for('login'))

   

    complaints = Complaint.query.filter_by(student_id=student.id).order_by(Complaint.id.desc()).all()
    months = generate_fees_for_student(student)
    products = Product.query.all()
    gate_passes = GatePass.query.filter_by(student_id=student_id).order_by(GatePass.date_requested.desc()).all()
    cart_items = Cart.query.filter_by(student_id=student.id).all()
    cart_count = sum(item.quantity for item in cart_items)
   


    return render_template(
        "student_dashboard.html",
        student=student,
        months=months,
        complaints=complaints,
        products=products,
        gate_passes=gate_passes,
        cart_count=cart_count,
        datetime=datetime
         # ✅ pass datetime to Jinja2
    )


@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    student_id = session.get('user_id')
    if not student_id:
        flash("You must be logged in to submit a complaint.", "danger")
        return redirect(url_for('student_dashboard'))

    title = request.form.get('title') or "No Title"
    description = request.form.get('complaint')

    if not description:
        flash("Complaint field cannot be empty.", "danger")
        return redirect(url_for('student_dashboard'))

    new_complaint = Complaint(title=title, description=description, student_id=student_id)
    db.session.add(new_complaint)
    db.session.commit()
    flash("Your complaint has been submitted successfully!", "success")
    return redirect(url_for('student_dashboard'))


@app.route('/admin/complaints', methods=['GET', 'POST'])
def admin_complaints():
    complaints = Complaint.query.order_by(Complaint.id.desc()).all()

    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')
        complaint = Complaint.query.get(complaint_id)
        if complaint:
            complaint.status = "Resolved"
            db.session.commit()
            flash("Complaint marked as resolved.", "success")
        return redirect(url_for('admin_complaints'))

    return render_template('admin_complaints.html', complaints=complaints)

@app.route('/resolve_complaint/<int:complaint_id>', methods=['POST'])
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = "Resolved"   # or whatever field you track
    try:
        db.session.commit()
        flash("Complaint marked as resolved!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error resolving complaint: " + str(e), "danger")
    return redirect(url_for('admin_dashboard'))



@app.route('/request_gate_pass', methods=['GET', 'POST'])
def request_gate_pass():
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    form_data = {'reason': '', 'leave_date': '', 'return_date': ''}
    success_message = None
    error_message = None

    if request.method == 'POST':
        reason = request.form.get('reason')
        leave_date_str = request.form.get('leave_date')
        return_date_str = request.form.get('return_date')

        form_data['reason'] = reason
        form_data['leave_date'] = leave_date_str
        form_data['return_date'] = return_date_str

        if not reason or not leave_date_str or not return_date_str:
            error_message = "All fields are required."
            return render_template('request_gate_pass.html', form_data=form_data, error_message=error_message)

        try:
            leave_date = datetime.strptime(leave_date_str, "%Y-%m-%d")
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
        except ValueError:
            error_message = "Invalid date format. Use YYYY-MM-DD."
            return render_template('request_gate_pass.html', form_data=form_data, error_message=error_message)

        if return_date < leave_date:
            error_message = "Return date cannot be earlier than leave date."
            return render_template('request_gate_pass.html', form_data=form_data, error_message=error_message)

        new_request = GatePass(
            student_id=session['user_id'],
            reason=reason,
            leave_date=leave_date,
            return_date=return_date,
            status='Pending'
        )
        db.session.add(new_request)
        db.session.commit()
        success_message = "Gate pass request submitted successfully!"
        return render_template('request_gate_pass.html', form_data={'reason':'','leave_date':'','return_date':''}, success_message=success_message)

    return render_template('request_gate_pass.html', form_data=form_data)


@app.route('/my_gate_passes')
def my_gate_passes():
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    student_id = session['user_id']
    gate_passes = GatePass.query.filter_by(student_id=student_id).order_by(GatePass.date_requested.desc()).all()
    
    return render_template('my_gate_passes.html', gate_passes=gate_passes)

@app.route('/view_cart')
def view_cart():
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    student_id = session['user_id']
    cart_items = Cart.query.filter_by(student_id=student_id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)
from flask import request

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'logged_in' not in session or session.get('role') != 'student':
        flash('Please log in to add items to cart.', 'danger')
        return redirect(url_for('login'))

    student_id = session['user_id']
    product = Product.query.get_or_404(product_id)

    cart_item = Cart.query.filter_by(student_id=student_id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += product.min_quantity
    else:
        cart_item = Cart(
            student_id=student_id,
            product_id=product.id,
            quantity=product.min_quantity
        )
        db.session.add(cart_item)

    db.session.commit()
    flash(f'{product.name} added to your cart!', 'success')

    # 🔥 Redirect back to the page where "Add to Cart" was clicked
    return redirect(request.referrer or url_for('view_cart'))

    
@app.route('/update_cart_quantity/<int:cart_id>', methods=['POST'])
def update_cart_quantity(cart_id):
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    cart_item = Cart.query.get_or_404(cart_id)
    new_quantity = int(request.form.get('quantity'))
    
    if new_quantity > 0:
        cart_item.quantity = new_quantity
        db.session.commit()
        flash('Cart updated successfully.', 'success')
    else:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'info')
        
    return redirect(url_for('view_cart'))
    
@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    cart_item = Cart.query.get_or_404(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))
@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    if 'logged_in' not in session or session.get('role') != 'student':
        flash('Please log in to checkout.', 'danger')
        return redirect(url_for('login'))

    student_id = session['user_id']   # ✅ correct key
    cart_items = Cart.query.filter_by(student_id=student_id).all()

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('view_cart'))

    # Save cart items as orders
    for item in cart_items:
        new_order = Order(
            student_id=student_id,
            product_id=item.product_id,
            quantity=item.quantity,
            total_price=item.product.price * item.quantity
        )
        db.session.add(new_order)

    # Clear cart after checkout
    Cart.query.filter_by(student_id=student_id).delete()
    db.session.commit()

    flash('Your order has been placed successfully!', 'success')
    return render_template('checkout_success.html')
from flask import request, redirect, url_for, flash

@app.route('/staff/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status in ["Pending", "Approved", "Delivered", "Cancelled"]:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} status updated to {new_status}.", "success")
    else:
        flash("Invalid status.", "error")

    return redirect(url_for('staff_dashboard'))
@app.route('/staff/order/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    order = Order.query.get(order_id)  # Get order by ID
    if order:
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully!', 'success')
    else:
        flash('Order not found!', 'error')
    return redirect(url_for('staff_dashboard'))

@app.route('/my_fees_status')
def my_fees_status():
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    student_id = session['user_id']
    student = Student.query.get(student_id)
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('login'))

    today = datetime.today()
    current_year = today.year
    current_month = today.month

    # Prepare next 12 months
    months = []
    for i in range(12):
        month_index = (current_month + i - 1) % 12 + 1
        year = current_year + ((current_month + i - 1) // 12)
        month_name = calendar.month_name[month_index]

        # Check if fee record exists
        fee = Fees.query.filter_by(student_id=student.id, month=month_name, year=year).first()
        if not fee:
            fee = Fees(
                student_id=student.id,
                month=month_name,
                year=year,
                amount_due=10000,
                amount_paid=0,
                status="Pending"
            )
            db.session.add(fee)

        # Determine dynamic status only for unpaid fees
        if fee.status != "Paid":
            if year < today.year or (year == today.year and month_index < today.month):
                fee.status = "Paid"  # previous months
            elif year == today.year and month_index == today.month:
                fee.status = "Pending"  # current month
            else:
                fee.status = "Not required now"  # future months

        months.append(fee)

    db.session.commit()  # commit all changes once

    return render_template('my_fees_status.html', months=months)



@app.route('/pay_fee/<int:fee_id>', methods=['GET','POST'])
def pay_fee(fee_id):
    if 'logged_in' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    fee = Fees.query.get_or_404(fee_id)

    # For simplicity, mark fee as fully paid
    fee.amount_paid = fee.amount_due
    fee.status = 'Paid'
    db.session.commit()

    flash(f'Payment for {fee.month} {fee.year} completed successfully!', 'success')
    return redirect(url_for('my_fees_status'))


def generate_fees_for_student(student):
    today = datetime.today()
    current_year = today.year
    current_month = today.month
    months = []

    for i in range(12):
        month_index = (current_month + i - 1) % 12 + 1
        year = current_year + ((current_month + i - 1) // 12)
        month_name = calendar.month_name[month_index]

        fee = Fees.query.filter_by(student_id=student.id, month=month_name, year=year).first()
        if not fee:
            fee = Fees(
                student_id=student.id,
                month=month_name,
                year=year,
                amount_due=10000,   # Default
                amount_paid=0,
                status="Pending"
            )
            db.session.add(fee)
            db.session.commit()

        months.append(fee)
    return months

@app.context_processor
def inject_cart_count():
    if 'user_id' in session and session.get('role') == 'student':
        student_id = session['user_id']
        cart_items = Cart.query.filter_by(student_id=student_id).all()
        cart_count = sum(item.quantity for item in cart_items)
    else:
        cart_count = 0
    return dict(cart_count=cart_count)

if __name__ == '__main__':
    with app.app_context():
        # Create initial users (admin/staff/student)
        create_initial_users()

        # Create default rooms if they don't exist
        if not Room.query.first():
            default_rooms = [
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
                Room(room_no='C-102', capacity=2, occupied=0)
            ]
            db.session.add_all(default_rooms)
            db.session.commit()
            print("Default rooms created.")

    # Run the Flask app
    app.run(host='127.0.0.1', port=5001, debug=True)
