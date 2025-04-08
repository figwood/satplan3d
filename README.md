# FastAPI Hello World Project

This project is a simple FastAPI application that connects to a MySQL database. It demonstrates how to set up a FastAPI application, connect to a database using environment variables, and define a basic route.

## Project Structure

```
fastapi-hello-world
├── app
│   ├── main.py          # Entry point of the FastAPI application
│   ├── database.py      # Database connection handling
│   └── models.py        # Data models for the application
├── .env                 # Environment variables for the project
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fastapi-hello-world
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory with the following content:
   ```
   DB_USER=root
   DB_PASSWORD=123456
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the application:**
   Open your browser and go to `http://127.0.0.1:8000`. You should see "Hello, World!".

## Additional Information

- Ensure that your MySQL server is running and accessible with the provided credentials.
- You can modify the database connection settings in `app/database.py` if needed.
- For more information on FastAPI, visit the [FastAPI documentation](https://fastapi.tiangolo.com/).