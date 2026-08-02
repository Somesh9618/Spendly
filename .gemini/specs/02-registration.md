# Spec: Registration

## Overview
User registration is a fundamental authentication step that allows new users to create accounts on Spendly. It processes form input, validates data, hashes passwords securely, stores new users in the database, and redirects them to the login screen, preparing the system for session-based user authentication.

## Depends on
- Database Setup (Step 1)

## Routes
- `GET /register` — Displays the registration form page — Public
- `POST /register` — Processes the user registration submission — Public

## Database changes
No database changes. The `users` table already has the required columns: `id`, `name`, `email`, `password_hash`, and `created_at`.

## Templates
- **Modify:**
  - `templates/register.html` — Ensure it renders validation error messages correctly if redirected with an `error` context variable.
  - `templates/login.html` — Add support for showing a success message (e.g. "Registration successful! Please log in.") when redirected from the registration page.

## Files to change
- `app.py` — Add `/register` routes and logic.
- `templates/login.html` — Add support for a success/info alert message.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] Navigating to `/register` successfully displays the registration form.
- [ ] Entering a valid name, a unique email, and a password (min. 8 characters) creates a new user in the `users` table with a hashed password.
- [ ] Attempting to register with an email that is already registered fails and displays the error message: "Email address is already registered."
- [ ] Attempting to register with a password under 8 characters fails and displays the error: "Password must be at least 8 characters long."
- [ ] Successful registration redirects the user to `/login` with a success message: "Registration successful! Please log in."
