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

# Predefined categories and payment methods (you can customize this)
CATEGORIES = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Groceries', 'Health', 'Rent', 'Other']
PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'Bank Transfer', 'Other']

# Initialize session state for manual expenses
if 'manual_expenses' not in st.session_state:
    st.session_state.manual_expenses = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Payment Method', 'Description'])

# Manual expense entry form
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

# CSV upload section
uploaded_file = st.file_uploader("Or upload an expenses CSV file", type=["csv"])

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

# Combine manual and uploaded data
if uploaded_df is not None:
    combined_df = pd.concat([uploaded_df, st.session_state.manual_expenses], ignore_index=True)
else:
    combined_df = st.session_state.manual_expenses.copy()

# Show analytics if any data present
if not combined_df.empty:
    st.subheader("Expense Data")
    st.dataframe(combined_df)

    # Total spending
    total_spent = combined_df['Amount'].sum()
    st.metric("Total Spending", f"${total_spent:,.2f}")

    # Spending by category
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

    # Personalized money-saving advice
    st.subheader("Personalized Money-Saving Advice")

    biggest_cat = category_sum.loc[category_sum['Amount'].idxmax()]['Category']
    biggest_cat_amount = category_sum['Amount'].max()

    advice_dict = {
        'Food': "Consider cooking at home more often and reducing takeout or restaurant meals.",
        'Transport': "Try carpooling, public transportation, or biking to save on fuel and maintenance.",
        'Utilities': "Reduce electricity and water usage; unplug devices when not in use.",
        'Entertainment': "Look for free or low-cost entertainment options like community events or streaming services.",
        'Groceries': "Plan meals, buy in bulk, and avoid impulse buys to cut grocery bills.",
        'Health': "Check if you can switch to a cheaper gym or home workouts; review medical bills carefully.",
        'Rent': "Evaluate if you can negotiate rent or consider downsizing if possible.",
        'Other': "Review your miscellaneous spending carefully and identify areas to cut back."
    }

    st.markdown(f"**Your biggest expense category:** {biggest_cat} (${biggest_cat_amount:,.2f})")
    st.markdown(f"**Tip:** {advice_dict.get(biggest_cat, 'Try to monitor this category and find ways to reduce costs.')}")

    monthly_avg = monthly_sum['Amount'].mean()
    st.markdown(f"**Your average monthly spending is:** ${monthly_avg:,.2f}")

    if monthly_avg > 3000:
        st.warning("Your spending is quite high. Consider setting a monthly budget and tracking expenses closely.")
    elif monthly_avg > 1500:
        st.info("Good job! Still, reviewing recurring expenses and subscriptions could help save more.")
    else:
        st.success("Great! Your spending is well controlled. Keep up the good budgeting habits.")

else:
    st.info("Add expenses manually above or upload a CSV file to start tracking and analyzing your spending.")
