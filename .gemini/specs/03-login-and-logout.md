# Spec: Login and Logout

## Overview
Implement session-based authentication in Spendly. This feature allows registered users to log in by validating their credentials against the database, store their session securely in Flask's session object, and log out by clearing the session. It also updates the navigation bar to dynamically reflect the authentication state.

## Depends on
- Database Setup (Step 1)
- Registration (Step 2)

## Routes
- `GET /login` — Displays the sign-in form page — Public
- `POST /login` — Processes login credentials, establishes session — Public
- `GET /logout` — Clears the user session and redirects — Logged-in only

## Database changes
No database changes. Relies on the existing `users` table.

## Templates
- **Modify:**
  - `templates/base.html` — Update navbar links to dynamically show "Profile" and "Logout" when a user is signed in, or "Sign in" and "Get started" when signed out, based on `g.user`.
  - `templates/login.html` — Ensure it displays error alerts if `error` context variable is provided.

## Files to change
- `app.py` — Add `/login` and `/logout` handlers, configure secret key for session signing, and implement a `before_request` hook to load the current logged-in user into Flask's `g.user`.
- `templates/base.html` — Modify the navigation bar link layout.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords checked with `werkzeug.security.check_password_hash`
- Set `app.secret_key` in `app.py` for session management (use a fallback development key or read from environment)
- Use a `before_request` handler to fetch the logged-in user from the database if `session.get('user_id')` is set, and store in Flask's `g` global context as `g.user`.
- Clear the session using `session.clear()` on logout.
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] Navigating to `/login` successfully displays the login form.
- [ ] Entering valid credentials redirects the user to the `/profile` page and sets `session['user_id']`.
- [ ] Entering an incorrect email or password fails and renders the login form with the error message: "Invalid email or password."
- [ ] Navigating to `/logout` clears the session, redirects the user to the landing page, and shows the logged-out state in the navigation.
- [ ] Nav bar displays "Profile" and "Logout" when authenticated.
- [ ] Nav bar displays "Sign in" and "Get started" when guest.
