# Sales Insight System

A complete Python/Flask + SQLite sales analytics and forecasting web application suitable for an academic BCA project.

## Features
- Admin and User authentication
- Role-based access
- Sales CRUD
- Product management
- CSV sales import
- Dashboard KPIs
- Product/month/region analysis
- Interactive Chart.js visualizations
- Linear Regression sales forecasting
- PDF report generation
- Clean responsive UI
- SQLite database with SQLAlchemy ORM
- Password hashing

## Default accounts
- Admin: admin@demo.com / admin123
- User: user@demo.com / user123

Change these passwords before any real deployment.

## Windows + VS Code setup

Open the project folder in VS Code terminal:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000

The database is created automatically at `instance/sales_insight.db`.

## CSV format
Use these columns:
Date, Product, Category, Quantity, Unit Price, Unit Cost, Region

Example:
2026-01-05,Laptop,Electronics,2,65000,52000,North

A sample file is included at `data/sample_sales.csv`.

## Academic note
The forecasting model uses Linear Regression as a clear and explainable baseline. Forecast quality depends on the amount and quality of historical data.
