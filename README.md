# EECE 435L - Lab 7: Python testing

**Student:** Joey Sade (202305993)

This project carries forward the Lab 5 Flask/SQLite user API and tests its database operations and HTTP endpoints with pytest. The database is created automatically when `app.py` is imported or run. A new database starts with an empty `users` table; the assignment's sample user is inserted by the tests.

## Setup and run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The API runs at `http://localhost:5000`. The Lab 5 Postman collection and environment are included for manual checks.

## Run tests

```powershell
python -m pytest -v test_user_Joey_Sade.py
```

Tests use a fresh temporary SQLite database for each case. They leave the real `database.db` untouched and cover database initialization, all five data functions, all four requested individual-user API functions, plus the list endpoint and error responses.

## API routes

| Method | Path |
| --- | --- |
| GET | `/api/users` |
| GET | `/api/users/<user_id>` |
| POST | `/api/users/add` |
| PUT | `/api/users/update` |
| DELETE | `/api/users/delete/<user_id>` |
