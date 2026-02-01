import streamlit as st # The core framework for the UI
import pandas as pd    # Used for data manipulation (DataFrames)
import numpy as np     # Used to generate random numerical data

# 1. Page Configuration: Sets the browser tab title and layout style.
# This MUST be the first Streamlit command in your script.
st.set_page_config(page_title="My First Streamlit App", layout="centered")

# 2. Title and Header: These create the main typography for your app.
st.title("Streamlit Assignment: Basic App")
st.header("Welcome to my Data Dashboard")

# 3. Sidebar: Using 'st.sidebar' puts these elements in a collapsible left panel.pip install streamlit
st.sidebar.header("User Settings")

# .text_input(label, default_value): Captures string input from the user.
user_name = st.sidebar.text_input("Enter your name:", "Guest")

# .slider(label, min, max, default): Captures an integer/float within a range.
data_size = st.sidebar.slider("Select number of data points:", 10, 100, 50)

# 4. Main Logic & Display: Streamlit supports f-strings and Markdown by default.
st.write(f"### Hello, {user_name}!")
st.write(f"Generating a random plot with {data_size} points...")

# Create a DataFrame: We use the 'data_size' variable from the slider 
# to determine how many rows of data to generate dynamically.
chart_data = pd.DataFrame(
    np.random.randn(data_size, 3), # Creates a matrix of random numbers
    columns=['Metric A', 'Metric B', 'Metric C']
)

# 5. Visualizations: Streamlit has built-in charting tools.
# This automatically detects the columns in the DataFrame and plots them.
st.line_chart(chart_data)

# Interactive Conditional: This block only runs if the checkbox is checked (True).
if st.checkbox("Show Raw Data"):
    st.subheader("Raw Data Table")
    # .dataframe() creates an interactive, scrollable table.
    st.dataframe(chart_data)

# 6. Success Message: A pre-styled green alert box for feedback.
st.success("App loaded successfully!")