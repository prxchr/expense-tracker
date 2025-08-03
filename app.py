import streamlit as st
import pandas as pd
import plotly.express as px
from prophet import Prophet
from datetime import datetime

st.set_page_config(
    page_title="Personal Expense Tracker & Forecasting",
    layout="wide"
)

st.title("Personal Expense Tracker & Forecasting")

# Predefined categories and payment methods (can add more if needed)
CATEGORIES = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Groceries', 'Health', 'Rent', 'Other']
PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'Bank Transfer', 'Other']

# Session state to keep manual expenses during the session
if 'manual_expenses' not in st.session_state:
    st.session_state.manual_expenses = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Payment Method', 'Description'])

# Section: Manual expense entry form
with st.expander("Add an expense manually"):
    with st.form("manual_expense_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("Date", datetime.today())
        with col2:
            category = st.selectbox("Category", CATEGORIES)
        with col3:
            amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
        payment_method = st.selectbox("Payment Method", PAYMENT_METHODS)
        description = st.text_input("Description")
        submitted = st.form_submit_button("Add Expense")

    if submitted:
        new_expense = pd.DataFrame({
            'Date': [pd.to_datetime(date)],
            'Category': [category],
            'Amount': [amount],
            'Payment Method': [payment_method],
            'Description': [description]
        })
        st.session_state.manual_expenses = pd.concat([st.session_state.manual_expenses, new_expense], ignore_index=True)
        st.success("Expense added!")

# Section: Optional CSV upload
uploaded_file = st.file_uploader("Or upload an expenses CSV file", type=["csv"])

# Load and validate CSV if uploaded
uploaded_df = None
if uploaded_file:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        required_cols = ['Date', 'Category', 'Amount', 'Payment Method', 'Description']
        if not all(col in uploaded_df.columns for col in required_cols):
            st.error(f"CSV missing required columns: {required_cols}")
            uploaded_df = None
        else:
            uploaded_df['Date'] = pd.to_datetime(uploaded_df['Date'])
            uploaded_df['Amount'] = pd.to_numeric(uploaded_df['Amount'], errors='coerce')
            uploaded_df = uploaded_df.dropna(subset=['Date', 'Amount'])
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        uploaded_df = None

# Combine manual expenses and uploaded CSV (if any)
if uploaded_df is not None:
    combined_df = pd.concat([uploaded_df, st.session_state.manual_expenses], ignore_index=True)
else:
    combined_df = st.session_state.manual_expenses.copy()

# If we have any expenses at all, show analytics and forecasting
if not combined_df.empty:
    st.subheader("Expense Data")
    st.dataframe(combined_df)

    # Total spending
    total_spent = combined_df['Amount'].sum()
    st.metric("Total Spending", f"${total_spent:,.2f}")

    # Spending by category pie chart
    category_sum = combined_df.groupby('Category')['Amount'].sum().reset_index()
    fig1 = px.pie(category_sum, values='Amount', names='Category', title='Spending by Category')
    st.plotly_chart(fig1, use_container_width=True)

    # Monthly spending bar chart
    combined_df['Month'] = combined_df['Date'].dt.to_period('M').dt.to_timestamp()
    monthly_sum = combined_df.groupby('Month')['Amount'].sum().reset_index()
    fig2 = px.bar(monthly_sum, x='Month', y='Amount', title='Monthly Spending')
    st.plotly_chart(fig2, use_container_width=True)

    # Forecasting with Prophet
    try:
        prophet_df = monthly_sum.rename(columns={'Month': 'ds', 'Amount': 'y'})
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(prophet_df)
        future = m.make_future_dataframe(periods=6, freq='M')
        forecast = m.predict(future)

        st.subheader("Expense Forecast (Next 6 Months)")
        fig3 = px.line(forecast, x='ds', y='yhat', title='Forecasted Monthly Spending')
        fig3.add_scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', line=dict(dash='dash'), name='Lower Confidence')
        fig3.add_scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', line=dict(dash='dash'), name='Upper Confidence')
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.warning(f"Forecasting skipped due to error: {e}")

else:
    st.info("Add expenses manually above or upload a CSV file to start tracking and analyzing your spending.")
