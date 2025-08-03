import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

st.title("💸 Personal Expense Tracker & Analytics Dashboard")

uploaded_file = st.file_uploader("Upload your expenses CSV file", type=["csv"])

if uploaded_file:
    try:
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

        # Monthly period column
        filtered['Month'] = filtered['Date'].dt.to_period("M")

        # KPIs
        total_spent = filtered['Amount'].sum()
        monthly_sum = filtered.groupby('Month')['Amount'].sum()
        avg_per_month = monthly_sum.mean() if not monthly_sum.empty else 0
        max_expense = filtered['Amount'].max() if not filtered.empty else 0
        num_transactions = filtered.shape[0]

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Spending", f"${total_spent:,.2f}")
        kpi2.metric("Avg Spend / Month", f"${avg_per_month:,.2f}")
        kpi3.metric("Highest Expense", f"${max_expense:,.2f}")
        kpi4.metric("Transactions", f"{num_transactions}")

        # Spending by Category Pie Chart
        st.subheader("Spending by Category")
        cat_sum = filtered.groupby('Category')['Amount'].sum().reset_index()
        fig1 = px.pie(
            cat_sum,
            values='Amount',
            names='Category',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Spending by Category"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Monthly Spending Line Chart
        st.subheader("Monthly Spending Over Time")
        monthly = monthly_sum.reset_index()
        monthly['Month'] = monthly['Month'].dt.to_timestamp()
        fig2 = px.line(
            monthly,
            x='Month',
            y='Amount',
            markers=True,
            color_discrete_sequence=["#636EFA"],
            title="Monthly Spending Trend"
        )
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error processing the file: {e}")
else:
    st.info("Please upload a CSV file to get started.")
