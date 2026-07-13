# Expense Tracker API

A REST API for tracking personal expenses. Users can sign up, log in, and manage their own set of expenses, protected by JWT authentication so each user only ever sees their own data.

## Requirements

- Python 3.x
- Flask
- Flask-SQLAlchemy
- PyJWT

No external database server required. This project uses SQLite, which stores everything in a single local file.

## Setup

1. Clone this repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install flask flask-sqlalchemy pyjwt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
   The server starts at `http://127.0.0.1:5000`, and `expenses.db` is created automatically on first run.

## Authentication

Most endpoints require a JWT, obtained by logging in. Include it on every protected request as a header:
```
Authorization: Bearer <your-token>
```

## Endpoints

### Sign up
```
POST /signup
```
```bash
curl -X POST http://127.0.0.1:5000/signup -H "Content-Type: application/json" -d "{\"username\": \"alex\", \"password\": \"mypassword123\"}"
```

### Log in
```
POST /login
```
Returns a JWT to use on all protected routes below.
```bash
curl -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d "{\"username\": \"alex\", \"password\": \"mypassword123\"}"
```

### Add an expense
```
POST /expenses
```
Requires auth.
```bash
curl -X POST http://127.0.0.1:5000/expenses -H "Content-Type: application/json" -H "Authorization: Bearer <your-token>" -d "{\"amount\": 45.50, \"category\": \"Groceries\", \"description\": \"Weekly grocery run\", \"date\": \"2026-07-11\"}"
```

### List expenses
```
GET /expenses
```
Requires auth. Returns only the logged-in user's expenses.
```bash
curl http://127.0.0.1:5000/expenses -H "Authorization: Bearer <your-token>"
```

Optional filters, passed as query parameters:

| Filter | Example |
|---|---|
| Past week | `/expenses?filter=week` |
| Past month | `/expenses?filter=month` |
| Last 3 months | `/expenses?filter=three-months` |
| Custom range | `/expenses?filter=custom&start=2026-06-01&end=2026-07-12` |

```bash
curl "http://127.0.0.1:5000/expenses?filter=week" -H "Authorization: Bearer <your-token>"
```

### Update an expense
```
PUT /expenses/<id>
```
Requires auth. Only works on expenses belonging to the logged-in user.
```bash
curl -X PUT http://127.0.0.1:5000/expenses/1 -H "Content-Type: application/json" -H "Authorization: Bearer <your-token>" -d "{\"amount\": 50.00, \"category\": \"Groceries\", \"description\": \"Updated grocery run\", \"date\": \"2026-07-11\"}"
```

### Delete an expense
```
DELETE /expenses/<id>
```
Requires auth. Only works on expenses belonging to the logged-in user.
```bash
curl -X DELETE http://127.0.0.1:5000/expenses/1 -H "Authorization: Bearer <your-token>"
```

## Data Models

### User
| Field | Type | Notes |
|---|---|---|
| id | integer | primary key |
| username | string | unique, required |
| password | string | stored as a hash, never plain text |

### Expense
| Field | Type | Notes |
|---|---|---|
| id | integer | primary key |
| amount | float | required |
| category | string | one of: Groceries, Leisure, Electronics, Utilities, Clothing, Health, Others |
| description | string | required |
| date | date | format `YYYY-MM-DD` |
| user_id | integer | foreign key linking the expense to its owner |

## Known Limitations

- The JWT secret key is currently hardcoded in `app.py` rather than loaded from an environment variable. Fine for local development, but should be moved to a config/env variable before any real deployment.
- `category` is stored as a plain string and not strictly validated against the 7 allowed values yet.