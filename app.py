import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from prophet import Prophet
from prophet.plot import plot_plotly
import base64
from io import StringIO

# ----- APP LAYOUT AND STYLE -----
st.set_page_config(page_title="Professional Expense Tracker", layout="wide")

st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem;}
    header {visibility: hidden;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .css-1offfwp {background-color: #f9f9f9; border-radius: 10px; padding: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("Professional Expense Tracker & AI-Powered Analytics")

# ----- FILE UPLOAD -----
uploaded_file = st.file_uploader("Upload your expenses CSV file (Date,Category,Amount,Payment Method,Description)", type=["csv"])

if uploaded_file:
    try:
        # --- Read & validate ---
        df = pd.read_csv(uploaded_file)
        expected_cols = ['Date', 'Category', 'Amount', 'Payment Method', 'Description']
        if not all(col in df.columns for col in expected_cols):
            st.error(f"CSV missing one or more required columns: {expected_cols}")
            st.stop()
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df.dropna(subset=['Date', 'Amount'], inplace=True)

        # --- Sidebar Filters ---
        st.sidebar.header("Filters & Settings")
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        date_range = st.sidebar.date_input("Select date range", [min_date, max_date])
        if len(date_range) != 2:
            st.sidebar.error("Select a valid date range")
            st.stop()
        
        categories = st.sidebar.multiselect("Filter by Category", options=df['Category'].unique(), default=df['Category'].unique())
        payments = st.sidebar.multiselect("Filter by Payment Method", options=df['Payment Method'].unique(), default=df['Payment Method'].unique())
        search_text = st.sidebar.text_input("Search Description")

        budget = st.sidebar.number_input("Set Monthly Budget ($)", min_value=0.0, step=50.0, value=0.0, help="Leave 0 for no budget tracking.")

        # --- Filter data ---
        filtered = df[
            (df['Date'] >= pd.to_datetime(date_range[0])) &
            (df['Date'] <= pd.to_datetime(date_range[1])) &
            (df['Category'].isin(categories)) &
            (df['Payment Method'].isin(payments))
        ]
        if search_text.strip():
            filtered = filtered[filtered['Description'].str.contains(search_text, case=False, na=False)]

        if filtered.empty:
            st.warning("No expenses match the filters. Please adjust filters.")
            st.stop()

        filtered['Month'] = filtered['Date'].dt.to_period("M")

        # --- KPIs ---
        total_spent = filtered['Amount'].sum()
        monthly_sum = filtered.groupby('Month')['Amount'].sum()
        avg_per_month = monthly_sum.mean()
        max_expense = filtered['Amount'].max()
        num_transactions = filtered.shape[0]

        # Compare with previous month
        prev_month = (pd.to_datetime(date_range[0]) - pd.offsets.MonthBegin(1)).to_period("M")
        prev_spent = monthly_sum.get(prev_month, np.nan)
        pct_change = ((avg_per_month - prev_spent) / prev_spent * 100) if not np.isnan(prev_spent) and prev_spent > 0 else None

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Spending", f"${total_spent:,.2f}")
        if pct_change is not None:
            change_symbol = "▲" if pct_change > 0 else "▼"
            col2.metric("Avg Spend / Month", f"${avg_per_month:,.2f}", f"{change_symbol} {abs(pct_change):.1f}% vs prev")
        else:
            col2.metric("Avg Spend / Month", f"${avg_per_month:,.2f}")
        col3.metric("Highest Expense", f"${max_expense:,.2f}")
        col4.metric("Transactions", f"{num_transactions}")

        # Budget alert
        if budget > 0:
            if total_spent > budget:
                st.error(f"🚨 You have exceeded your monthly budget of ${budget:,.2f} by ${total_spent - budget:,.2f}!")
            else:
                st.success(f"🎉 You are within your monthly budget of ${budget:,.2f}")

        # --- Spending by Category Pie ---
        st.subheader("Spending by Category")
        cat_sum = filtered.groupby('Category')['Amount'].sum().reset_index()
        fig_cat = px.pie(cat_sum, values='Amount', names='Category', title="Category Breakdown",
                         color_discrete_sequence=px.colors.qualitative.Dark24)
        st.plotly_chart(fig_cat, use_container_width=True)

        # --- Monthly Spending Trend ---
        st.subheader("Monthly Spending Over Time")
        monthly = monthly_sum.reset_index()
        monthly['Month'] = monthly['Month'].dt.to_timestamp()
        fig_month = px.line(monthly, x='Month', y='Amount', markers=True, title="Monthly Spending Trend",
                            color_discrete_sequence=["#1f77b4"])
        st.plotly_chart(fig_month, use_container_width=True)

        # --- Cumulative Spending ---
        st.subheader("Cumulative Spending Over Time")
        filtered_sorted = filtered.sort_values('Date')
        filtered_sorted['Cumulative'] = filtered_sorted['Amount'].cumsum()
        fig_cum = px.area(filtered_sorted, x='Date', y='Cumulative', title="Cumulative Spending")
        st.plotly_chart(fig_cum, use_container_width=True)

        # --- Expense Forecasting (AI) ---
        st.subheader("Forecast Next 3 Months Spending (Prophet Model)")

        # Prepare data for Prophet
        prophet_df = monthly.rename(columns={'Month': 'ds', 'Amount': 'y'})
        model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=3, freq='M')
        forecast = model.predict(future)

        fig_forecast = plot_plotly(model, forecast)
        st.plotly_chart(fig_forecast, use_container_width=True)

        # --- Detailed Transactions Table ---
        st.subheader("Filtered Transactions")
        st.dataframe(filtered.sort_values('Date', ascending=False).reset_index(drop=True), use_container_width=True)

        # --- CSV Download Link ---
        csv = filtered.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="filtered_expenses.csv">Download Filtered Data as CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

        # --- Smart Insights ---
        st.subheader("Smart Insights")
        if pct_change is not None:
            if pct_change > 20:
                st.info("🔴 Alert: Your average monthly spending has increased by more than 20% compared to the previous month.")
            elif pct_change < -20:
                st.info("🟢 Good job! Your average monthly spending has decreased significantly compared to last month.")
            else:
                st.info("Your spending is stable compared to last month.")
        else:
            st.info("Not enough data for month-over-month comparison.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload a CSV file with these columns: Date, Category, Amount, Payment Method, Description")
