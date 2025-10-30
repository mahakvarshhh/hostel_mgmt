from app import db
from models import Admin

def reset_admin_password(username, new_password):
    from app import app
    with app.app_context():
        admin = Admin.query.filter_by(username=username).first()
        if admin:
            admin.set_password(new_password)
            db.session.commit()
            print(f"Password for '{username}' has been reset to '{new_password}'.")
        else:
            print(f"Admin '{username}' not found.")

if __name__ == "__main__":
    reset_admin_password("admin", "098")

