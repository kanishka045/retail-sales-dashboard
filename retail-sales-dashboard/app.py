import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme / styling ----------
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(20, 184, 166, .10), rgba(59, 130, 246, .06));
        border: 1px solid rgba(128,128,128,.20);
        padding: 16px 18px;
        border-radius: 14px;
    }
    [data-testid="stMetricLabel"] {font-size: .92rem;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .subtitle {color: #64748b; margin-top: -10px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Retail Sales Analytics")
st.markdown('<p class="subtitle">Explore sales, profitability, products, and customer segments.</p>', unsafe_allow_html=True)

# ---------- Load data ----------
DATA_PATH = Path(__file__).parent / "Sample - Superstore(1).csv"

@st.cache_data
def load_data(file_bytes=None):
    if file_bytes is not None:
        from io import BytesIO
        try:
            data = pd.read_csv(BytesIO(file_bytes), encoding="utf-8-sig")
        except UnicodeDecodeError:
            data = pd.read_csv(BytesIO(file_bytes), encoding="cp1252")
    else:
        try:
            data = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        except UnicodeDecodeError:
            data = pd.read_csv(DATA_PATH, encoding="cp1252")

    data.columns = data.columns.str.strip()
    for col in ["Order Date", "Ship Date"]:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")
    for col in ["Sales", "Profit", "Quantity", "Discount"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data

if DATA_PATH.exists():
    df = load_data()
else:
    st.info("Upload your Superstore CSV to get started.")
    uploaded = st.file_uploader("Choose the retail sales CSV file", type=["csv"])
    if uploaded is None:
        st.stop()
    df = load_data(uploaded.getvalue())

required = {"Order Date", "Sales", "Profit", "Order ID", "Category", "Region", "Product Name"}
missing = required - set(df.columns)
if missing:
    st.error("The dataset is missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

# ---------- Sidebar filters ----------
st.sidebar.title("🎛️ Dashboard Filters")
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

def multiselect_filter(label, column):
    if column not in df.columns:
        return None
    values = sorted(df[column].dropna().astype(str).unique().tolist())
    return st.sidebar.multiselect(f"{label}", values, default=values)

regions = multiselect_filter("Region", "Region")
categories = multiselect_filter("Category", "Category")
segments = multiselect_filter("Customer segment", "Segment")
ship_modes = multiselect_filter("Ship mode", "Ship Mode")

filtered = df[
    df["Order Date"].dt.date.between(start_date, end_date)
].copy()
if regions is not None:
    filtered = filtered[filtered["Region"].astype(str).isin(regions)]
if categories is not None:
    filtered = filtered[filtered["Category"].astype(str).isin(categories)]
if segments is not None:
    filtered = filtered[filtered["Segment"].astype(str).isin(segments)]
if ship_modes is not None:
    filtered = filtered[filtered["Ship Mode"].astype(str).isin(ship_modes)]

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
    st.stop()

# ---------- KPI row ----------
total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
orders = filtered["Order ID"].nunique()
units = filtered["Quantity"].sum() if "Quantity" in filtered else 0
customers = filtered["Customer ID"].nunique() if "Customer ID" in filtered else 0
profit_margin = (total_profit / total_sales * 100) if total_sales else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Profit", f"${total_profit:,.0f}")
k3.metric("Orders", f"{orders:,}")
k4.metric("Units Sold", f"{units:,.0f}")
k5.metric("Profit Margin", f"{profit_margin:.1f}%")

st.caption(f"Showing {len(filtered):,} rows · {customers:,} unique customers · Data from {start_date:%d %b %Y} to {end_date:%d %b %Y}")

# ---------- Interactive sales trend ----------
st.subheader("Sales Performance")
trend_metric = st.selectbox(
    "Choose what to track over time",
    options=["Sales", "Profit", "Quantity", "Discount"],
    index=0,
    help="Change this selection to update the monthly trend chart.",
)
trend_aggregation = "sum"
monthly = (
    filtered.assign(Month=filtered["Order Date"].dt.to_period("M").dt.to_timestamp())
    .groupby("Month", as_index=False)
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum"),
        Discount=("Discount", "mean"),
    )
    .sort_values("Month")
)
left, right = st.columns([1.65, 1])
with left:
    trend_title = {
        "Sales": "Monthly Sales Trend",
        "Profit": "Monthly Profit Trend",
        "Quantity": "Monthly Units Sold",
        "Discount": "Average Monthly Discount",
    }[trend_metric]
    fig = px.line(
        monthly, x="Month", y=trend_metric, markers=True,
        title=trend_title, template="plotly_white",
        color_discrete_sequence=["#0D9488"],
    )
    fig.update_traces(line_width=3, marker_size=7)
    fig.update_layout(
        height=360, margin=dict(l=10,r=10,t=55,b=10),
        xaxis_title="", yaxis_title=trend_metric,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
with right:
    cat = filtered.groupby("Category", as_index=False).agg(Sales=("Sales", "sum")).sort_values("Sales")
    fig = px.bar(cat, x="Sales", y="Category", orientation="h", text_auto=".2s",
                 title="Sales by Category", template="plotly_white",
                 color="Sales", color_continuous_scale="Teal")
    fig.update_layout(height=360, margin=dict(l=10,r=10,t=55,b=10), xaxis_title="Sales ($)", yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Profit & product analysis ----------
st.subheader("Profitability & Product Insights")
left, right = st.columns(2)
with left:
    region = filtered.groupby("Region", as_index=False).agg(Profit=("Profit", "sum")).sort_values("Profit")
    fig = px.bar(region, x="Region", y="Profit", title="Profit by Region",
                 template="plotly_white", text_auto=".2s", color="Profit",
                 color_continuous_scale="Teal")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=55,b=10), xaxis_title="", yaxis_title="Profit ($)", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
with right:
    top_products = (
        filtered.groupby("Product Name", as_index=False)
        .agg(Profit=("Profit", "sum"), Sales=("Sales", "sum"), Quantity=("Quantity", "sum"))
        .sort_values("Profit", ascending=False).head(10).sort_values("Profit")
    )
    fig = px.bar(top_products, x="Profit", y="Product Name", orientation="h",
                 title="Top 10 Products by Profit", template="plotly_white",
                 text_auto=".2s", color="Profit", color_continuous_scale="Teal")
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=55,b=10), xaxis_title="Profit ($)", yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Category detail and data table ----------
left, right = st.columns(2)
with left:
    if "Sub-Category" in filtered.columns:
        subcat = filtered.groupby("Sub-Category", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).sort_values("Sales", ascending=False)
        fig = px.bar(subcat, x="Sales", y="Sub-Category", orientation="h",
                     title="Sales by Sub-Category", template="plotly_white",
                     color="Profit", color_continuous_scale="RdYlGn",
                     hover_data=["Profit"])
        fig.update_layout(height=470, margin=dict(l=10,r=10,t=55,b=10), xaxis_title="Sales ($)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
with right:
    if "Segment" in filtered.columns:
        segment = filtered.groupby("Segment", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        fig = px.pie(segment, names="Segment", values="Sales", hole=.58,
                     title="Sales by Customer Segment", template="plotly_white")
        fig.update_layout(height=470, margin=dict(l=10,r=10,t=55,b=10), legend_title="")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Filtered Transaction Details")
search = st.text_input("Search product, order, customer, city, or state", placeholder="Type a keyword...")
table = filtered.copy()
if search.strip():
    searchable = [c for c in ["Product Name", "Order ID", "Customer Name", "City", "State", "Category", "Sub-Category"] if c in table.columns]
    mask = pd.Series(False, index=table.index)
    for col in searchable:
        mask |= table[col].astype(str).str.contains(search.strip(), case=False, na=False)
    table = table[mask]

display_cols = [c for c in ["Order Date", "Order ID", "Customer Name", "Region", "Category", "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit"] if c in table.columns]
st.dataframe(table[display_cols].sort_values("Order Date", ascending=False), use_container_width=True, hide_index=True)

csv = table.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Download filtered data as CSV", data=csv, file_name="retail_sales_filtered.csv", mime="text/csv")

st.markdown("---")
st.caption("Built with Streamlit, Pandas, and Plotly · Values are calculated from the selected records.")
