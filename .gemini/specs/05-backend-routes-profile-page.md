# Spec: Backend Routes for Profile Page

## Overview
This feature connects the `/profile` page to the SQLite database. It replaces the hardcoded context dictionaries in the profile route with dynamic queries that fetch the logged-in user's information, aggregate their spending stats (total spent, transaction count, top category), list their most recent transactions, and calculate their category-wise spending breakdown. This ensures the profile page displays real-time user data.

## Depends on
- Step 1: Database Setup (schema and seed function)
- Step 2: Registration
- Step 3: Login + Logout
- Step 4: Profile Page (initial template and design layout)

## Routes
- `GET /profile` — Renders the profile page with live database data — Logged-in only (redirects to `/login` if not authenticated)

## Database changes
No database changes. Relies on the existing `users` and `expenses` tables.

## Templates
- **Modify:**
  - `templates/profile.html` — Update layout to handle empty states gracefully (e.g., showing friendly messages like "No recent transactions" or "No spending recorded yet" when the user has no expenses log, and ensuring bar classes and percentages render safely).

## Files to change
- `app.py` — Replace the hardcoded view logic in `/profile` with database queries.
- `templates/profile.html` — Add fallback elements for empty states.
- `tests/test_profile.py` — Update or add test cases to verify database-driven profile statistics and handling of users with no expenses.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- **No SQLAlchemy or ORMs** — Use raw sqlite3 via `get_db()`.
- **Parameterized queries only** — Never string-format or interpolate user inputs or session variables into SQL.
- **Session Protection** — Ensure access is blocked and redirects to `/login` if `session.get("user_id")` is not present.
- **Graceful Empty States** — Safely handle users with zero transactions to avoid `ZeroDivisionError` when computing percentages. If there are no expenses, default the total spent to `₹0.00`, transaction count to `0`, top category to `N/A`, and display empty state placeholder messages.
- **Currency Formatting** — Format all currency values using standard Indian Rupees representation (e.g., `₹1,850.00` or `₹25.50`).
- **Dynamic CSS Classes** — Category badge and progress bar classes must be dynamically derived using CSS-safe class names, e.g., `badge-` + `category.lower()` or `bar-` + `category.lower()`.
- **Date Formatting** — Format the member-since date (`created_at` from `users` table) to a readable string (e.g., "August 2, 2026") in Python.
- **Pagination/Limit** — Limit the recent transactions display to a maximum of 5 rows, ordered by date descending (and then ID descending for secondary ordering).

## Definition of done
- [ ] Navigating to `/profile` while logged in as a new user with 0 expenses displays:
  - Total Spent as `₹0.00`
  - Transaction count as `0`
  - Top category as `N/A`
  - A friendly fallback message for empty transactions (e.g., "No recent transactions")
  - A friendly fallback message for empty category breakdown (e.g., "No spending recorded yet")
- [ ] Navigating to `/profile` while logged in as the demo user retrieves and displays their actual expenses:
  - Total Spent matches the sum of their expenses
  - Transaction count matches their total count of expenses
  - Top category corresponds to the category with the highest sum of expenses
  - List of up to 5 most recent transactions is shown, sorted from newest to oldest
  - Category breakdown lists percentages and sum for each category, rendering the correct progress bar widths matching their percentages
- [ ] All data is fetched dynamically using parameterized SQLite queries via `get_db()`.
- [ ] Password and authentication verification still function correctly, and unauthorized access to `/profile` is blocked.
- [ ] All automated tests in `tests/test_profile.py` and `tests/test_login_logout.py` run and pass.
