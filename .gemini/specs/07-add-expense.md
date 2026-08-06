# Spec: Add Expense

## Overview
This feature allows logged-in users to log new expenses. It provides an intuitive input form where users can record the spent amount, select a predefined category, specify the date of the expense, and optionally add a description. Recording new expenses is critical for the expense tracker, enabling real-time financial tracking and dynamic dashboard updates.

## Depends on
- Step 4: Profile Page
- Step 5: Backend Routes for Profile Page
- Step 6: Date Filter for Profile Page

## Routes
- `GET /expenses/add` — Renders the add expense form page — Logged-in only (redirects to `/login` if not authenticated)
- `POST /expenses/add` — Processes the add expense form submission, validates fields, saves the new expense to the database, and redirects to `/profile` — Logged-in only (redirects to `/login` if not authenticated)

## Database changes
No database changes. Relies on the existing `expenses` table schema.

## Templates
- **Create:**
  - `templates/add_expense.html` — The new add expense form template. It must extend `base.html` and contain:
    - A form with `action="/expenses/add"` and `method="POST"`.
    - Input for amount: `<input type="number" step="0.01" name="amount" id="amount" required>`
    - Select dropdown for category: `<select name="category" id="category" required>` with options for the fixed categories: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`.
    - Input for date: `<input type="date" name="date" id="date" required>`
    - Textarea/input for description: `<textarea name="description" id="description" ...>` (optional)
    - Submit button ("Add Expense").
    - Cancel link (points back to `/profile`).
    - Error message container (if validation fails on submission).
- **Modify:**
  - `templates/profile.html` — Add a link/button styled to match the theme (e.g., "Add Expense" button in the summary/nav area) that directs to `/expenses/add`.

## Files to change
- `app.py` — Replace the placeholder `add_expense` route handler with the implementation supporting both GET and POST. Validate amount, category, date, and description on POST. Insert the validated expense into the database. Handle errors and preserve form data on failure.
- `templates/profile.html` — Add the "Add Expense" button to the template layout.

## Files to create
- `templates/add_expense.html` — Form UI for adding a new expense.
- `tests/test_add_expense.py` — Add integration/unit tests for the add expense feature (GET loading, POST success, POST validation failures).

## New dependencies
No new dependencies.

## Rules for implementation
- **No SQLAlchemy or ORMs** — Use raw sqlite3 via `get_db()`.
- **Parameterised queries only** — Never string-format or interpolate user inputs or session variables into SQL. Always pass inputs as parameters to `cursor.execute()`.
- **Passwords hashed with werkzeug** — Ensure standard authentication is respected.
- **Use CSS variables** — Never hardcode hex values. Use existing variables (like color variables) defined in `static/css/style.css`.
- **All templates extend `base.html`**.
- **Form validation**:
  - The amount must be a positive number greater than 0. If it is 0 or negative, or not a valid number, display the error message: `"Amount must be greater than 0."`.
  - The category must be one of the predefined list (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`).
  - The date must be a valid date in `YYYY-MM-DD` format.
  - The description is optional but should not exceed 200 characters. If it does, show the error: `"Description must be 200 characters or less."`.
- **Error handling**:
  - If validation fails, re-render `templates/add_expense.html` displaying the specific error message and preserving the user's input values.
- **Success notification**:
  - Upon successful insertion, redirect to the profile page (which will display the updated stats and transactions).

## Definition of done
- [ ] Logged-out users attempting to access `/expenses/add` are redirected to `/login`.
- [ ] Logged-in users visiting `/expenses/add` see the Add Expense form with fields for Amount, Category, Date, and Description.
- [ ] The Category input is a dropdown menu pre-populated with exactly the 7 fixed categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other.
- [ ] Submitting the form with valid data (e.g., amount = `50.00`, category = `Food`, date = `2026-08-06`, description = `Lunch`) successfully inserts the record in the database and redirects the user to `/profile`.
- [ ] The newly added expense is visible in the recent transactions list on the profile page, and the total spent/transaction count/category breakdown adjust dynamically.
- [ ] Submitting the form with a negative or zero amount displays the error message `"Amount must be greater than 0."` and preserves form inputs.
- [ ] Submitting the form with an empty date or invalid date format displays an appropriate validation error message and preserves inputs.
- [ ] Submitting the form with a description longer than 200 characters displays the error message `"Description must be 200 characters or less."` and preserves inputs.
- [ ] The "Cancel" link on the add expense page correctly redirects back to `/profile`.
- [ ] All database interactions use parameterized SQL.
- [ ] All automated tests in `tests/test_add_expense.py` pass.
