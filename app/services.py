import io
from datetime import date
import pandas as pd
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

def sales_dataframe(sales):
    rows = []
    for s in sales:
        rows.append({
            "Date": s.date, "Product": s.product.name if s.product else "Unknown",
            "Category": s.product.category if s.product else "Unknown",
            "Quantity": s.quantity, "Revenue": s.revenue, "Profit": s.profit,
            "Region": s.region
        })
    return pd.DataFrame(rows)

def monthly_summary(sales):
    df = sales_dataframe(sales)
    if df.empty:
        return []
    df["Date"] = pd.to_datetime(df["Date"])
    g = df.groupby(df["Date"].dt.to_period("M")).agg(Revenue=("Revenue","sum"), Profit=("Profit","sum"), Quantity=("Quantity","sum")).reset_index()
    g["Date"] = g["Date"].astype(str)
    return g.to_dict("records")

def forecast(sales, periods=6):
    monthly = monthly_summary(sales)
    if len(monthly) < 3:
        return {"error": "At least 3 months of sales history are required for forecasting."}
    y = [float(x["Revenue"]) for x in monthly]
    X = [[i] for i in range(len(y))]
    model = LinearRegression().fit(X, y)
    preds = model.predict([[len(y)+i] for i in range(periods)])
    last = pd.Period(monthly[-1]["Date"], freq="M")
    labels = [str(last + i) for i in range(1, periods+1)]
    return {
        "labels": labels,
        "values": [round(float(v), 2) for v in preds],
        "r2": round(float(model.score(X, y)), 4),
        "months_used": len(y)
    }

def build_pdf(sales):
    monthly = monthly_summary(sales)
    total_revenue = sum(s.revenue for s in sales)
    total_profit = sum(s.profit for s in sales)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Sales Insight System - Sales Report", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Generated report containing {len(sales)} sales transactions.", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph(f"Total Revenue: ₹{total_revenue:,.2f}", styles["Heading3"]),
        Paragraph(f"Total Profit: ₹{total_profit:,.2f}", styles["Heading3"]),
        Spacer(1, 12),
    ]
    data = [["Month", "Revenue", "Profit", "Quantity"]]
    for r in monthly:
        data.append([r["Date"], f"₹{r['Revenue']:,.2f}", f"₹{r['Profit']:,.2f}", str(r["Quantity"])])
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f2937")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(1,1),(-1,-1),"RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f3f4f6")])
    ]))
    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf
