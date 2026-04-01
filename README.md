# SatPlan3D API

SatPlan3D is a FastAPI backend for satellite planning workflows. It combines user authentication, satellite and sensor management, TLE-driven orbit propagation, precomputed track generation, observation opportunity search, and order management in a single MySQL-backed service.

The codebase is structured as a pragmatic API service rather than a generic FastAPI starter. If you are integrating a frontend or building automation around Earth observation planning, this repository provides the core backend pieces.

## Highlights

- JWT-based authentication with admin-only operations for protected write endpoints.
- Satellite registration from TLE data.
- Automatic one-week track and sensor path precomputation after TLE updates.
- Track lookup with fallback to real-time orbital calculation.
- Observation opportunity search within a geographic bounding box.
- Order creation, listing, inspection, update, and deletion.
- MySQL schema bootstrap via `init.sql` and automatic SQLAlchemy table creation on startup.

## Current API Scope

The application currently exposes these functional areas:

- **Authentication**
  - `POST /api/login`
  - `POST /change-password`
- **Satellites and TLE management**
  - `GET /api/satellite/list`
  - `POST /api/satellite`
  - `PUT /api/satellite/{noard_id}`
  - `PUT /api/tle`
- **Tracks and sensor paths**
  - `GET /api/track-points`
  - `GET /api/path-points`
- **Coverage and scheduling**
  - `GET /api/coverage`
  - `POST /api/schedule`
- **Orders**
  - `GET /api/order/list`
  - `POST /api/order`
  - `GET /api/order/{order_id}/info`
  - `PUT /api/order/{order_id}`
  - `DELETE /api/order/{order_id}`

Interactive API docs are available through FastAPI once the server is running:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Project Structure

```text
satplan3d
├── app
│   ├── main.py                 # FastAPI entry point and router registration
│   ├── database.py             # SQLAlchemy engine and session setup
│   ├── models.py               # ORM models
│   ├── dependencies.py         # Auth and permission dependencies
│   ├── security.py             # Password hashing and JWT helpers
│   ├── routers
│   │   ├── auth.py             # Login and password change
│   │   ├── satellites.py       # Satellite, TLE, and sensor-related operations
│   │   ├── tracks.py           # Orbit track and path queries
│   │   ├── coverage.py         # Coverage endpoint scaffold
│   │   ├── schedule.py         # Observation opportunity search
│   │   └── orders.py           # Order CRUD endpoints
│   ├── schemas
│   │   └── base.py             # Pydantic request and response schemas
│   └── utils
│       └── coordinate_transform.py
├── init.sql                    # Example schema and seed data for MySQL
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build file
├── README.md                   # English documentation
└── README.zh.md                # Chinese documentation
```

## Tech Stack

- **FastAPI** for the web API and OpenAPI documentation.
- **SQLAlchemy** for ORM and database sessions.
- **MySQL** with `mysql-connector-python` as the database backend.
- **pyorbital** for TLE-based orbital propagation.
- **NumPy** and **SciPy** for numerical support.
- **python-jose** and **passlib** for JWT auth and password hashing.

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd satplan3d
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database connection

Create a `.env` file in the project root:

```env
DB_USER=root
DB_PASSWORD=123456
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=satplan3d
```

`app/database.py` reads these values to build the SQLAlchemy connection string.

### 5. Initialize the database

You can load the provided schema and sample data from `init.sql` into MySQL before starting the service.

Example:

```bash
mysql -u root -p satplan3d < init.sql
```

The application also calls `models.Base.metadata.create_all(bind=engine)` at startup, which creates missing tables defined by the ORM models.

### 6. Start the API server

```bash
uvicorn app.main:app --reload
```

### 7. Verify the service

- API root: `http://127.0.0.1:8000/api`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Authentication Model

- `POST /api/login` returns a bearer token.
- Protected admin actions, such as satellite creation and TLE updates, require a valid JWT.
- OAuth2 bearer token extraction is configured in `app/dependencies.py`.

At the moment, JWT settings such as `SECRET_KEY` and `ALGORITHM` are defined directly in `app/security.py` rather than loaded from environment variables.

## Planning Workflow

A typical backend workflow looks like this:

1. Import or create a satellite using TLE data.
2. Store the parsed TLE in the database.
3. Precompute one week of tracks and sensor paths at a 20-second interval.
4. Query track points or path points for a time window.
5. Search for observation opportunities over a target area.
6. Persist selected opportunities as planning orders.

This design keeps common query paths fast by precomputing track and sensor path data while still allowing fallback orbital calculations when cached track data is unavailable.

## Development Notes

- Route registration happens in `app/main.py`.
- Shared request and response models are defined in `app/schemas/base.py`.
- Database entities are defined in `app/models.py`.
- Coordinate-related calculations live in `app/utils/coordinate_transform.py`.
- Logging is configured with the standard Python `logging` module.

## Known Gaps

- The `GET /api/coverage` endpoint is currently a placeholder and returns an empty list.
- Some configuration values that would usually live in environment variables are still hardcoded in `app/security.py`.
- There is no migration setup in the repository; schema evolution is currently manual.
- The repository does not include an automated test suite.

## FAQ

### How do I add a new route?

Create a new router module under `app/routers` and register it in `app/main.py`.

### How are tracks generated?

When TLE data is created or updated, the service precomputes one week of track points and sensor paths in 20-second steps.

### Does the API compute tracks in real time?

Yes. `GET /api/track-points` first checks the database for precomputed tracks and falls back to live orbital calculation if necessary.

### Is this ready for production?

It is a functional backend service, but production hardening is still needed around configuration management, migrations, test coverage, and endpoint completeness.