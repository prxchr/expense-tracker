Personal Expense Tracker & Forecasting App
Overview
This is a web-based personal expense tracker and analytics dashboard built with Python and Streamlit. It allows users to manually enter expenses or upload CSV files, visualize spending patterns, and forecast future expenses.
The app provides:
•	Data upload and manual input of expenses with customizable categories and payment methods.
•	Interactive charts displaying spending by category and monthly spending trends.
•	Time series forecasting of monthly expenses using Facebook Prophet.
•	Date range filtering to analyze expenses over any selected period.
•	Personalized money-saving advice based on spending behavior.
Features
•	Expense input via manual form or CSV upload.
•	Data cleaning and validation.
•	Dynamic filtering by date range.
•	Pie charts and bar charts for spending analysis.
•	Forecasting with confidence intervals.
•	Practical, personalized financial tips.
Technologies Used
•	Python
•	Streamlit for web app interface
•	Pandas for data manipulation
•	Plotly Express for interactive charts
•	Facebook Prophet for forecasting
How to Run
•	Clone the repository.
•	Install dependencies:
pip install -r requirements.txt
•	Run the app:
streamlit run app.py
•	Open the local URL provided in the terminal.
CSV File Requirements
If uploading a CSV file, it must contain the following columns:
•	Date (format: YYYY-MM-DD)
•	Category
•	Amount (numeric)
•	Payment Method
•	Description
