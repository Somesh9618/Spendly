# Spec: Date Filter for Profile Page

## Overview
This feature adds a date range filter to the profile page. It allows logged-in users to filter their spending data (Summary Stats, Category Breakdown, and Recent Transactions) by selecting a Start Date and an End Date. This enables users to analyze their spending patterns over specific time periods rather than just viewing their lifetime statistics and the most recent 5 transactions.

## Depends on
- Step 4: Profile Page
- Step 5: Backend Routes for Profile Page

## Routes
No new routes. The existing route is modified to support optional query parameters:
- `GET /profile` — Renders the profile page with filtered or all-time database data — Logged-in only (redirects to `/login` if not authenticated)
  - Query parameters:
    - `start_date` (optional): Filter expenses on or after this date (format: `YYYY-MM-DD`).
    - `end_date` (optional): Filter expenses on or before this date (format: `YYYY-MM-DD`).

## Database changes
No database changes. Relies on the existing `users` and `expenses` tables.

## Templates
- **Modify:**
  - `templates/profile.html` — Add a filter form above the stats and transaction content (or within the layout where visually pleasing). The form must contain:
    - Start date input: `<input type="date" name="start_date" id="start_date" ...>`
    - End date input: `<input type="date" name="end_date" id="end_date" ...>`
    - A "Filter" submit button.
    - A "Clear" button (which resets the filters by redirecting back to `/profile`).
    - Error message alert (if dates are invalid).
    - Preserved values: the inputs must retain the current filter values from the URL query parameters.

## Files to change
- `app.py` — Update the `/profile` route handler to:
  - Retrieve `start_date` and `end_date` from `request.args`.
  - Validate that the dates are in the correct format (`YYYY-MM-DD`).
  - If `start_date` is greater than `end_date`, show a validation error: `"Start date cannot be after end date."` and do not query the database for transactions (defaulting stats to empty/zero values).
  - Dynamically build the SQL queries for stats, recent transactions, and category breakdown by appending date conditions:
    - If `start_date` is provided: `AND date >= ?`
    - If `end_date` is provided: `AND date <= ?`
  - Pass the current `start_date`, `end_date`, and any error messages to `render_template`.
- `templates/profile.html` — Integrate the date filter form UI and display error messages if present.
- `tests/test_profile.py` — Add automated unit tests to verify the date filtering logic.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- **No SQLAlchemy or ORMs** — Use raw sqlite3 via `get_db()`.
- **Parameterized queries only** — Never string-format or interpolate user inputs or session variables into SQL. Always pass dates as parameters to `cursor.execute()`.
- **Use CSS variables** — Never hardcode hex values.
- **All templates extend `base.html`**.
- **Date validation** — Dates must be validated in Python using `datetime.strptime(date_str, "%Y-%m-%d")` to ensure they are valid dates and correctly formatted.
- **Persist form inputs** — The date input elements must show the currently selected start and end dates if they are set.
- **Error handling** — If start date is after end date, display an error message in the UI: `"Start date cannot be after end date."` and show empty stats (`₹0.00`, `0` transactions, `N/A` top category).
- **Pagination/Limit** — Limit the filtered transactions display to a maximum of 5 rows, ordered by date descending, ID descending.

## Definition of done
- [ ] The profile page displays two date input fields (Start Date and End Date), a "Filter" button, and a "Clear" button.
- [ ] Clicking "Filter" with a valid date range (e.g. `start_date=2026-08-01` and `end_date=2026-08-03`) displays:
  - Total Spent, Transaction Count, and Top Category reflecting only the expenses in that range.
  - Category breakdown percentages and totals matching only the expenses in that range.
  - A list of up to 5 transactions that fall within that range (inclusive), sorted by date descending, ID descending.
- [ ] If only one date is specified (e.g., `start_date` only), it filters from that date forward.
- [ ] If only the other date is specified (e.g., `end_date` only), it filters up to that date.
- [ ] If both inputs are blank, it shows all-time data.
- [ ] If `start_date` is later than `end_date`, the page displays the error message `"Start date cannot be after end date."`, and shows empty states for stats (`₹0.00`, `0`, `N/A`), empty category breakdown, and empty transactions.
- [ ] After applying a filter, the input fields continue to show the selected dates.
- [ ] Clicking the "Clear" button resets both inputs and displays all-time data.
- [ ] All database queries are parameterized and safe.
- [ ] All automated tests pass successfully.
