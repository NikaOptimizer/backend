# backend

Django API bridge for Nika Optimizer.

The backend sits between the React frontend and the existing Python repositories. It owns web/API concerns such as routing, request validation, response shapes, auth-ready workflow state, and future background job dispatch. It should not reimplement domain logic from `data-manager`, `no-calculator`, `strategist`, or `fisher`.

## Current API template

Database-backed behavior is intentionally not implemented yet. These endpoints exist so the frontend and backend can agree on routes before the database schema is created:

- `GET /api/strategies/` — strategy list placeholder
- `GET /api/strategies/<strategy_id>/` — strategy detail placeholder
- `PUT /api/strategies/` — create strategy placeholder

Each endpoint returns `501 Not Implemented` with a JSON body explaining that database setup is pending.

## Local commands

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python manage.py check
python manage.py test
python manage.py runserver
```
