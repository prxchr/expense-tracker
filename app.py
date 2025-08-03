import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Personal Expense Tracker & Analytics Dashboard")

uploaded_file = st.file_uploader("Upload your expenses CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Basic cleaning
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Date', 'Amount'])

    st.subheader("Raw Data")
    st.write(df)

    # Total spending
    total_spent = df['Amount'].sum()
    st.metric("Total Spending", f"${total_spent:.2f}")

    # Spending by Category
    category_sum = df.groupby('Category')['Amount'].sum().reset_index()
    fig1 = px.pie(category_sum, values='Amount', names='Category', title='Spending by Category')
    st.plotly_chart(fig1)

    # Spending over Time
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    monthly_sum = df.groupby('Month')['Amount'].sum().reset_index()
    fig2 = px.bar(monthly_sum, x='Month', y='Amount', title='Monthly Spending')
    st.plotly_chart(fig2)
else:
    st.info("Please upload a CSV file to get started.")
