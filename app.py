# pyrefly: ignore [missing-import]
from flask import Flask, render_template
from database.db import init_db, seed_db

app = Flask(__name__)

# Initialize and seed the database on app startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login")
def login():
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
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
