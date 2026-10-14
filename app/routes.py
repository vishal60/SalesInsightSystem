from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime
from . import db
from .models import User, Product, Sale
from .services import sales_dataframe, monthly_summary, forecast, build_pdf
import pandas as pd

main = Blueprint("main", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access is required.", "danger")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)
    return wrapped

@main.route("/")
def index():
    return redirect(url_for("main.dashboard") if "user_id" in session else url_for("main.login"))

@main.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            session.update(user_id=user.id, name=user.name, role=user.role)
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/dashboard")
@login_required
def dashboard():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    revenue = sum(s.revenue for s in sales)
    profit = sum(s.profit for s in sales)
    qty = sum(s.quantity for s in sales)
    products = {}
    for s in sales:
        products.setdefault(s.product.name, 0)
        products[s.product.name] += s.revenue
    top_product = max(products, key=products.get) if products else "—"
    return render_template("dashboard.html", sales=sales[:8], revenue=revenue, profit=profit,
                           quantity=qty, top_product=top_product)

@main.route("/sales")
@login_required
def sales():
    rows = Sale.query.order_by(Sale.date.desc()).all()
    return render_template("sales.html", sales=rows)

@main.route("/sales/add", methods=["GET","POST"])
@login_required
def add_sale():
    products = Product.query.order_by(Product.name).all()
    if request.method == "POST":
        try:
            p = Product.query.get(int(request.form["product_id"]))
            qty = int(request.form["quantity"])
            if not p or qty <= 0:
                raise ValueError
            s = Sale(date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
                     product_id=p.id, quantity=qty, unit_price=float(request.form["unit_price"]),
                     unit_cost=float(request.form["unit_cost"]), region=request.form["region"])
            db.session.add(s); db.session.commit()
            flash("Sales record added successfully.", "success")
            return redirect(url_for("main.sales"))
        except Exception:
            flash("Please enter valid sales information.", "danger")
    return render_template("sale_form.html", products=products, sale=None)

@main.route("/sales/<int:sale_id>/delete", methods=["POST"])
@admin_required
def delete_sale(sale_id):
    s = Sale.query.get_or_404(sale_id)
    db.session.delete(s); db.session.commit()
    flash("Sales record deleted.", "success")
    return redirect(url_for("main.sales"))

@main.route("/products")
@login_required
def products():
    return render_template("products.html", products=Product.query.order_by(Product.name).all())

@main.route("/products/add", methods=["POST"])
@admin_required
def add_product():
    p = Product(name=request.form["name"], category=request.form["category"],
                unit_price=float(request.form["unit_price"]), unit_cost=float(request.form["unit_cost"]))
    db.session.add(p); db.session.commit()
    flash("Product added.", "success")
    return redirect(url_for("main.products"))

@main.route("/import", methods=["GET","POST"])
@login_required
def import_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.lower().endswith(".csv"):
            flash("Please upload a CSV file.", "danger")
            return redirect(url_for("main.import_csv"))
        try:
            df = pd.read_csv(file)
            required = ["Date","Product","Category","Quantity","Unit Price","Unit Cost","Region"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                flash("Missing columns: " + ", ".join(missing), "danger")
                return redirect(url_for("main.import_csv"))
            count = 0
            for _, row in df.iterrows():
                p = Product.query.filter_by(name=str(row["Product"])).first()
                if not p:
                    p = Product(name=str(row["Product"]), category=str(row["Category"]),
                                 unit_price=float(row["Unit Price"]), unit_cost=float(row["Unit Cost"]))
                    db.session.add(p); db.session.flush()
                db.session.add(Sale(date=pd.to_datetime(row["Date"]).date(), product_id=p.id,
                                    quantity=int(row["Quantity"]), unit_price=float(row["Unit Price"]),
                                    unit_cost=float(row["Unit Cost"]), region=str(row["Region"])))
                count += 1
            db.session.commit()
            flash(f"{count} records imported successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Import failed. Check the CSV format and values.", "danger")
        return redirect(url_for("main.sales"))
    return render_template("import.html")

@main.route("/analytics")
@login_required
def analytics():
    sales = Sale.query.all()
    df = sales_dataframe(sales)
    monthly = monthly_summary(sales)
    product_data = {}
    region_data = {}
    if not df.empty:
        product_data = df.groupby("Product")["Revenue"].sum().sort_values(ascending=False).round(2).to_dict()
        region_data = df.groupby("Region")["Revenue"].sum().round(2).to_dict()
    return render_template("analytics.html", monthly=monthly, product_data=product_data, region_data=region_data)

@main.route("/forecast")
@login_required
def forecast_page():
    result = forecast(Sale.query.all(), 6)
    return render_template("forecast.html", result=result)

@main.route("/report.pdf")
@login_required
def report_pdf():
    return send_file(build_pdf(Sale.query.order_by(Sale.date).all()), as_attachment=True,
                     download_name="sales_insight_report.pdf", mimetype="application/pdf")

@main.route("/admin/users")
@admin_required
def users():
    return render_template("users.html", users=User.query.order_by(User.created_at.desc()).all())

@main.route("/admin/users/add", methods=["POST"])
@admin_required
def add_user():
    email = request.form["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("main.users"))
    u = User(name=request.form["name"], email=email,
             password_hash=generate_password_hash(request.form["password"]),
             role=request.form["role"])
    db.session.add(u); db.session.commit()
    flash("User created successfully.", "success")
    return redirect(url_for("main.users"))
