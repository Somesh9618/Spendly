# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, session, g, abort
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
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

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    error_msg = None
    valid_start = None
    valid_end = None

    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            valid_start = start_date
        except ValueError:
            error_msg = "Invalid start date format."

    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            valid_end = end_date
        except ValueError:
            error_msg = "Invalid end date format."

    if not error_msg and valid_start and valid_end and valid_start > valid_end:
        error_msg = "Start date cannot be after end date."

    if error_msg:
        stats = {
            "total_spent": "₹0.00",
            "transaction_count": 0,
            "top_category": "N/A"
        }
        transactions = []
        category_breakdown = []
    else:
        # Build dynamic queries using parameterized logic
        conditions = ["user_id = ?"]
        params = [session["user_id"]]

        if valid_start:
            conditions.append("date >= ?")
            params.append(valid_start)
        if valid_end:
            conditions.append("date <= ?")
            params.append(valid_end)

        where_clause = " AND ".join(conditions)

        # SUBAGENT_2_STATS_START
        # Calculate total spent
        cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {where_clause}", params)
        total_spent_val = cursor.fetchone()[0]
        total_spent_str = f"₹{total_spent_val:,.2f}" if total_spent_val is not None else "₹0.00"
        
        # Calculate transaction count
        cursor.execute(f"SELECT COUNT(*) FROM expenses WHERE {where_clause}", params)
        tx_count_val = cursor.fetchone()[0]
        
        # Calculate top category
        cursor.execute(f"""
            SELECT category 
            FROM expenses 
            WHERE {where_clause} 
            GROUP BY category 
            ORDER BY SUM(amount) DESC 
            LIMIT 1
        """, params)
        top_cat_row = cursor.fetchone()
        top_category_str = top_cat_row["category"] if top_cat_row else "N/A"
        
        stats = {
            "total_spent": total_spent_str,
            "transaction_count": tx_count_val,
            "top_category": top_category_str
        }
        # SUBAGENT_2_STATS_END

        # SUBAGENT_1_TRANSACTIONS_START
        cursor.execute(f"""
            SELECT id, date, description, category, amount 
            FROM expenses 
            WHERE {where_clause} 
            ORDER BY date DESC, id DESC 
            LIMIT 5
        """, params)
        db_expenses = cursor.fetchall()
        
        transactions = []
        for exp in db_expenses:
            cat_lower = exp["category"].lower() if exp["category"] else "other"
            transactions.append({
                "id": exp["id"],
                "date": exp["date"],
                "description": exp["description"] if exp["description"] else "",
                "category": exp["category"],
                "amount": f"₹{exp['amount']:,.2f}",
                "badge_class": f"badge-{cat_lower}"
            })
        # SUBAGENT_1_TRANSACTIONS_END

        # SUBAGENT_3_BREAKDOWN_START
        # Calculate total spent to compute percentages
        cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {where_clause}", params)
        grand_total_row = cursor.fetchone()
        grand_total = grand_total_row[0] if grand_total_row and grand_total_row[0] is not None else 0.0
        
        cursor.execute(f"""
            SELECT category, SUM(amount) AS total 
            FROM expenses 
            WHERE {where_clause} 
            GROUP BY category 
            ORDER BY total DESC
        """, params)
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
    return render_template(
        "profile.html", 
        user_info=user_info, 
        stats=stats, 
        transactions=transactions, 
        category_breakdown=category_breakdown,
        start_date=start_date,
        end_date=end_date,
        error_msg=error_msg
    )



@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        error = None
        amount = None

        # Amount validation
        if not amount_str:
            error = "Amount must be greater than 0."
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    error = "Amount must be greater than 0."
            except ValueError:
                error = "Amount must be greater than 0."

        # Category validation
        if not error and category not in categories:
            error = "Invalid category."

        # Date validation
        if not error:
            if not date_str:
                error = "Invalid date format."
            else:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    error = "Invalid date format."

        # Description validation
        if not error and len(description) > 200:
            error = "Description must be 200 characters or less."

        if error:
            return render_template(
                "add_expense.html",
                error=error,
                amount=amount_str,
                category=category,
                date=date_str,
                description=description,
                categories=categories
            )

        # Database insertion
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (session["user_id"], amount, category, date_str, description or None))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template(
                "add_expense.html",
                error="An error occurred while saving the expense. Please try again.",
                amount=amount_str,
                category=category,
                date=date_str,
                description=description,
                categories=categories
            )
        conn.close()
        return redirect(url_for("profile"))

    # GET request - pre-populate date with today
    today_str = datetime.today().strftime("%Y-%m-%d")
    return render_template(
        "add_expense.html",
        date=today_str,
        categories=categories
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, amount, category, date, description 
        FROM expenses 
        WHERE id = ?
    """, (id,))
    expense = cursor.fetchone()

    if expense is None or expense["user_id"] != session["user_id"]:
        conn.close()
        abort(404)

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        error = None
        amount = None

        # Amount validation
        if not amount_str:
            error = "Amount must be greater than 0."
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    error = "Amount must be greater than 0."
            except ValueError:
                error = "Amount must be greater than 0."

        # Category validation
        if not error and category not in categories:
            error = "Invalid category."

        # Date validation
        if not error:
            if not date_str:
                error = "Invalid date format."
            else:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    error = "Invalid date format."

        # Description validation
        if not error and len(description) > 200:
            error = "Description must be 200 characters or less."

        if error:
            conn.close()
            return render_template(
                "edit_expense.html",
                error=error,
                expense={
                    "id": id,
                    "amount": amount_str,
                    "category": category,
                    "date": date_str,
                    "description": description
                },
                categories=categories
            )

        try:
            cursor.execute("""
                UPDATE expenses
                SET amount = ?, category = ?, date = ?, description = ?
                WHERE id = ? AND user_id = ?
            """, (amount, category, date_str, description or None, id, session["user_id"]))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template(
                "edit_expense.html",
                error="An error occurred while updating the expense. Please try again.",
                expense={
                    "id": id,
                    "amount": amount_str,
                    "category": category,
                    "date": date_str,
                    "description": description
                },
                categories=categories
            )
        conn.close()
        return redirect(url_for("profile"))

    # GET request - map sqlite row to dict and pre-populate
    expense_data = {
        "id": expense["id"],
        "amount": f"{expense['amount']:.2f}",
        "category": expense["category"],
        "date": expense["date"],
        "description": expense["description"] or ""
    }
    conn.close()
    return render_template(
        "edit_expense.html",
        expense=expense_data,
        categories=categories
    )


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
