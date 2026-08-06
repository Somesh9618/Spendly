# Spec: Edit Expense

## Overview
This feature allows logged-in users to edit their existing expenses. It provides an edit form pre-populated with the expense's current values (Amount, Category, Date, and Description), allowing users to correct mistakes or update expense details. For security and integrity, users are strictly restricted to editing only expenses that belong to their own account.

## Depends on
- Step 4: Profile Page
- Step 5: Backend Routes for Profile Page
- Step 6: Date Filter for Profile Page
- Step 7: Add Expense

## Routes
- `GET /expenses/<int:id>/edit` — Renders the edit expense form pre-populated with the expense details — Logged-in only (redirects to `/login` if not authenticated)
- `POST /expenses/<int:id>/edit` — Processes the edit expense form submission, validates fields, updates the record in the database, and redirects to `/profile` — Logged-in only (redirects to `/login` if not authenticated)

## Database changes
No database changes. Relies on the existing `expenses` table schema.

## Templates
- **Create:**
  - `templates/edit_expense.html` — The edit expense form template. It must extend `base.html` and contain:
    - A form with `action="/expenses/<id>/edit"` and `method="POST"`.
    - Input for amount: `<input type="number" step="0.01" name="amount" id="amount" value="{{ amount }}" required>`
    - Select dropdown for category: `<select name="category" id="category" required>` pre-selected with the current category of the expense. Predefined list: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`.
    - Input for date: `<input type="date" name="date" id="date" value="{{ date }}" required>`
    - Textarea/input for description: `<textarea name="description" id="description" ...>{{ description }}</textarea>` (optional)
    - Submit button ("Save Changes").
    - Cancel link (points back to `/profile`).
    - Error message container (if validation fails on submission).
- **Modify:**
  - `templates/profile.html` — Add an "Actions" column to the recent transactions table. Next to each transaction, display an edit icon or link (e.g., Lucide `pencil` or text link "Edit") pointing to the edit route for that expense.

## Files to change
- `app.py` — 
  - Update the `/profile` route to retrieve the expense `id` from the database and pass it into the `transactions` list context.
  - Implement `/expenses/<int:id>/edit` GET and POST routes. Ensure the expense exists and belongs to the currently logged-in user. If not, return HTTP 404 (Not Found).
  - Validate amount, category, date, and description on POST. Keep user input on validation error and render `edit_expense.html` with the error. Update the record using parameterized SQL upon successful validation.
- `templates/profile.html` — Add an "Actions" column in the recent transactions table with a link to `/expenses/<id>/edit`.

## Files to create
- `templates/edit_expense.html` — Form UI for editing an existing expense.
- `tests/test_edit_expense.py` — Unit and integration tests for the edit expense feature.

## New dependencies
No new dependencies.

## Rules for implementation
- **No SQLAlchemy or ORMs** — Use raw sqlite3 via `get_db()`.
- **Parameterised queries only** — Never string-format or interpolate user inputs or session variables into SQL. Always pass inputs as parameters to `cursor.execute()`.
- **Passwords hashed with werkzeug** — Ensure standard authentication is respected.
- **Use CSS variables** — Never hardcode hex values. Use existing variables defined in `static/css/style.css`.
- **All templates extend `base.html`**.
- **Access Control & Ownership Verification**:
  - A user must only be able to view/edit expenses they own. If the requested expense does not exist or does not belong to the logged-in user, the app must abort with HTTP 404.
- **Form validation**:
  - The amount must be a positive number greater than 0. If it is 0 or negative, display the error message: `"Amount must be greater than 0."`.
  - The category must be one of the predefined list (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`).
  - The date must be a valid date in `YYYY-MM-DD` format.
  - The description is optional but should not exceed 200 characters. If it does, show the error: `"Description must be 200 characters or less."`.
- **Error handling**:
  - If validation fails, re-render `templates/edit_expense.html` displaying the specific error message and preserving the user's input values.
- **Success handling**:
  - Redirect the user back to `/profile` on success.

## Definition of done
- [ ] Logged-out users attempting to access `/expenses/<id>/edit` are redirected to `/login`.
- [ ] Logged-in users attempting to edit a non-existent expense ID or an expense ID belonging to another user receive a 404 error page.
- [ ] Logged-in users visiting `/expenses/<id>/edit` for their own expense see the form pre-populated with the correct Amount, Category, Date, and Description.
- [ ] Submitting the form with valid updated data (e.g., changing amount from `25.50` to `30.00`) successfully updates the record in the database and redirects the user to `/profile`.
- [ ] The updated expense values are visible in the recent transactions list on the profile page, and the quick stats / category breakdown adjust accordingly.
- [ ] Submitting the form with a negative or zero amount displays the error message `"Amount must be greater than 0."` and preserves form inputs.
- [ ] Submitting the form with an empty date or invalid date format displays an appropriate validation error message and preserves inputs.
- [ ] Submitting the form with a description longer than 200 characters displays the error message `"Description must be 200 characters or less."` and preserves inputs.
- [ ] Clicking the "Cancel" link on the edit expense page correctly redirects back to `/profile` without modifying the database.
- [ ] All database queries are parameterized and safe.
- [ ] All automated tests in `tests/test_edit_expense.py` pass.
