# Spec: Delete Expense

## Overview
This feature allows logged-in users to delete their existing expenses. It provides a delete link next to each transaction row on the profile dashboard, complete with a client-side confirmation dialog to prevent accidental deletions. To ensure database integrity and security, users are strictly restricted to deleting only expenses that belong to their own account.

## Depends on
- Step 4: Profile Page
- Step 5: Backend Routes for Profile Page
- Step 6: Date Filter for Profile Page
- Step 7: Add Expense
- Step 8: Edit Expense

## Routes
- `GET /expenses/<int:id>/delete` — Processes the deletion of the specified expense if authorized, and redirects to `/profile` — Logged-in only (redirects to `/login` if not authenticated)

## Database changes
No database changes. Relies on the existing `expenses` table schema.

## Templates
- **Modify:**
  - `templates/profile.html` — Update the "Actions" column in the recent transactions table to include a "Delete" link alongside the "Edit" link.
    - Style the link with Lucide `trash-2` icon and the `--danger` color variable (dark red).
    - Add a browser confirmation popup (`onclick="return confirm('Are you sure you want to delete this expense?');"`) to confirm deletion before navigating.

## Files to change
- `app.py` — Replace the placeholder `delete_expense` route handler with the actual implementation:
  - Guard the route for logged-in users (redirect to `/login` if not authenticated).
  - Retrieve the expense row by `id`.
  - If the expense does not exist or its `user_id` does not match the currently logged-in user, return HTTP 404 (Not Found).
  - Perform the deletion from the database using a parameterized SQL query:
    ```sql
    DELETE FROM expenses WHERE id = ? AND user_id = ?
    ```
  - Commit the transaction, close the connection, and redirect the user back to the profile page.
- `templates/profile.html` — Add the delete action button link inside the recent transactions table body.

## Files to create
- `tests/test_09-delete-expense.py` — Unit and integration tests for the delete expense feature.

## New dependencies
No new dependencies.

## Rules for implementation
- **No SQLAlchemy or ORMs** — Use raw sqlite3 via `get_db()`.
- **Parameterised queries only** — Never string-format or interpolate user inputs or session variables into SQL. Always pass inputs as parameters to `cursor.execute()`.
- **Passwords hashed with werkzeug** — Ensure standard authentication is respected.
- **Use CSS variables** — Never hardcode hex values. Use existing variables (like `--danger` and `--border`) defined in `static/css/style.css`.
- **All templates extend `base.html`**.
- **Access Control & Ownership Verification**:
  - A user must only be able to delete expenses they own. If the requested expense does not exist or does not belong to the logged-in user, the app must abort with HTTP 404.
- **Accidental Deletion Prevention**:
  - The delete link must have an inline browser confirmation box to ask the user to confirm before proceeding.

## Definition of done
- [ ] Logged-out users attempting to access `/expenses/<id>/delete` are redirected to `/login`.
- [ ] Logged-in users attempting to delete a non-existent expense ID or an expense ID belonging to another user receive a 404 error page.
- [ ] Clicking the "Delete" link on the profile page shows a confirmation dialog.
- [ ] Confirming the deletion successfully removes the record from the database, redirects the user back to `/profile`, and the quick stats / category breakdown / transaction list update dynamically.
- [ ] Canceling the deletion dialog keeps the expense in the database and keeps the user on the profile page.
- [ ] All database queries are parameterized and safe.
- [ ] All automated tests in `tests/test_09-delete-expense.py` pass.
