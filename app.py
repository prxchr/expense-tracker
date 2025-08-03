import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

st.title("💸 Personal Expense Tracker & Analytics Dashboard")

uploaded_file = st.file_uploader("Upload your expenses CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Date', 'Amount'])

    # Sidebar filters
    st.sidebar.header("Filters")
    min_date, max_date = st.sidebar.date_input(
        "Select date range",
        [df['Date'].min(), df['Date'].max()]
    )
    categories = st.sidebar.multiselect(
        "Select categories",
        options=df['Category'].unique(),
        default=df['Category'].unique()
    )

    # Filter data
    filtered = df[
        (df['Date'] >= pd.to_datetime(min_date)) &
        (df['Date'] <= pd.to_datetime(max_date)) &
        (df['Category'].isin(categories))
    ]

    # KPIs
    total_spent = filtered['Amount'].sum()
    avg_per_month = filtered.groupby(filtered['Date'].dt.to_period("M")).sum()['Amount'].mean()
    max_expense = filtered['Amount'].max()
    num_transactions = filtered.shape[0]

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Spending", f"${total_spent:,.2f}")
    kpi2.metric("Avg Spend / Month", f"${avg_per_month:,.2f}")
    kpi3.metric("Highest Expense", f"${max_expense:,.2f}")
    kpi4.metric("Transactions", f"{num_transactions}")

    # Charts
    st.subheader("Spending by Category")
    cat_sum = filtered.groupby('Category')['Amount'].sum().reset_index()
    fig1 = px.pie(cat_sum, values='Amount', names='Category', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Monthly Spending Over Time")
    monthly = filtered.groupby(filtered['Date'].dt.to_period('M')).sum().reset_index()
    monthly['Date'] = monthly['Date'].dt.to_timestamp()
    fig2 = px.line(monthly, x='Date', y='Amount', markers=True, color_discrete_sequence=["#636EFA"])
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Please upload a CSV file to get started.")
