# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, session, g
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash
import os
from database.db import init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-spendly")

# Initialize and seed the database on app startup
with app.app_context():
    init_db()
    seed_db()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
        g.user = cursor.fetchone()
        conn.close()



# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
            
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long.")
            
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email is already taken
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            conn.close()
            return render_template("register.html", error="Email address is already registered.")
            
        # Hash password and store
        password_hash = generate_password_hash(password)
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            """, (name, email, password_hash))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template("register.html", error="An error occurred during registration. Please try again.")
            
        conn.close()
        return redirect(url_for("login", success="Registration successful! Please log in."))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            return render_template("login.html", error="Invalid email or password.")
            
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")
            
        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_info = {
        "name": g.user["name"] if (g.user and hasattr(g.user, "keys") and "name" in g.user.keys()) else (g.user[1] if g.user and len(g.user) > 1 else "Demo User"),
        "email": g.user["email"] if (g.user and hasattr(g.user, "keys") and "email" in g.user.keys()) else (g.user[2] if g.user and len(g.user) > 2 else "demo@spendly.com"),
        "member_since": "August 2, 2026"
    }

    stats = {
        "total_spent": "₹18,240.00",
        "transaction_count": 34,
        "top_category": "Food"
    }

    transactions = [
        {"date": "2026-08-01", "description": "Dinner at local diner", "category": "Food", "amount": "₹1,850.00", "badge_class": "badge-food"},
        {"date": "2026-08-02", "description": "Monthly internet subscription", "category": "Bills", "amount": "₹1,200.00", "badge_class": "badge-bills"},
        {"date": "2026-08-03", "description": "New running sneakers", "category": "Shopping", "amount": "₹4,500.00", "badge_class": "badge-shopping"}
    ]

    category_breakdown = [
        {"category": "Food", "amount": "₹8,500.00", "percentage": 47, "bar_class": "bar-food"},
        {"category": "Bills", "amount": "₹6,200.00", "percentage": 34, "bar_class": "bar-bills"},
        {"category": "Shopping", "amount": "₹3,540.00", "percentage": 19, "bar_class": "bar-shopping"}
    ]

    return render_template("profile.html", user_info=user_info, stats=stats, transactions=transactions, category_breakdown=category_breakdown)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


@app.route("/debug-db")
def debug_db():
    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT id, user_id, amount, category, date, description, created_at FROM expenses")
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template("debug_db.html", users=users, expenses=expenses)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
