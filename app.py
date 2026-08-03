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

    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()

    # Get user info and format join date
    cursor.execute("SELECT name, email, created_at FROM users WHERE id = ?", (session["user_id"],))
    user_row = cursor.fetchone()
    
    from datetime import datetime
    try:
        created_at_dt = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S")
        member_since_str = created_at_dt.strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        member_since_str = "August 2, 2026"

    user_info = {
        "name": user_row["name"] if user_row else "Demo User",
        "email": user_row["email"] if user_row else "demo@spendly.com",
        "member_since": member_since_str
    }

    # SUBAGENT_2_STATS_START
    # Calculate total spent
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (session["user_id"],))
    total_spent_val = cursor.fetchone()[0]
    total_spent_str = f"₹{total_spent_val:,.2f}" if total_spent_val is not None else "₹0.00"
    
    # Calculate transaction count
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (session["user_id"],))
    tx_count_val = cursor.fetchone()[0]
    
    # Calculate top category
    cursor.execute("""
        SELECT category 
        FROM expenses 
        WHERE user_id = ? 
        GROUP BY category 
        ORDER BY SUM(amount) DESC 
        LIMIT 1
    """, (session["user_id"],))
    top_cat_row = cursor.fetchone()
    top_category_str = top_cat_row["category"] if top_cat_row else "N/A"
    
    stats = {
        "total_spent": total_spent_str,
        "transaction_count": tx_count_val,
        "top_category": top_category_str
    }
    # SUBAGENT_2_STATS_END

    # SUBAGENT_1_TRANSACTIONS_START
    cursor.execute("""
        SELECT date, description, category, amount 
        FROM expenses 
        WHERE user_id = ? 
        ORDER BY date DESC, id DESC 
        LIMIT 5
    """, (session["user_id"],))
    db_expenses = cursor.fetchall()
    
    transactions = []
    for exp in db_expenses:
        cat_lower = exp["category"].lower() if exp["category"] else "other"
        transactions.append({
            "date": exp["date"],
            "description": exp["description"] if exp["description"] else "",
            "category": exp["category"],
            "amount": f"₹{exp['amount']:,.2f}",
            "badge_class": f"badge-{cat_lower}"
        })
    # SUBAGENT_1_TRANSACTIONS_END

    # SUBAGENT_3_BREAKDOWN_START
    # Calculate total spent to compute percentages
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (session["user_id"],))
    grand_total_row = cursor.fetchone()
    grand_total = grand_total_row[0] if grand_total_row and grand_total_row[0] is not None else 0.0
    
    cursor.execute("""
        SELECT category, SUM(amount) AS total 
        FROM expenses 
        WHERE user_id = ? 
        GROUP BY category 
        ORDER BY total DESC
    """, (session["user_id"],))
    db_breakdown = cursor.fetchall()
    
    category_breakdown = []
    for row in db_breakdown:
        cat_total = row["total"]
        pct = round((cat_total / grand_total) * 100) if grand_total > 0 else 0
        cat_lower = row["category"].lower() if row["category"] else "other"
        category_breakdown.append({
            "category": row["category"],
            "amount": f"₹{cat_total:,.2f}",
            "percentage": pct,
            "bar_class": f"bar-{cat_lower}"
        })
    # SUBAGENT_3_BREAKDOWN_END

    conn.close()
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
