
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import joblib
import os

# Set page configuration
st.set_page_config(
    page_title="Jaya Jaya Maju - Employee Attrition Dashboard",
    page_icon="👥",
    layout="wide"
)

# Load the data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("./data/employee_data_clean.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("data/employee_data_clean.csv")
        except FileNotFoundError:
            st.error("Could not find the employee data file. Please check the file path.")
            df = pd.DataFrame()
    return df

# Load the machine learning model
@st.cache_resource
def load_model():
    try:
        model = joblib.load("./models/gb_attrition_prediction_model.joblib")
    except FileNotFoundError:
        try:
            model = joblib.load("models/gb_attrition_prediction_model.joblib")
        except FileNotFoundError:
            st.error("Could not find the machine learning model. Please check the file path.")
            model = None
    return model


# Function to create age groups
def create_age_groups(df):
    df_copy = df.copy()
    df_copy['AgeGroup'] = pd.cut(
        df_copy['Age'], 
        bins=[18, 25, 35, 45, 55, 65],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65']
    )
    return df_copy

# Function to create income groups
def create_income_groups(df):
    df_copy = df.copy()
    df_copy['IncomeGroup'] = pd.cut(
        df_copy['MonthlyIncome'],
        bins=[0, 2000, 5000, 10000, 20000],
        labels=['0-2K', '2K-5K', '5K-10K', '10K-20K']
    )
    return df_copy

# Function to calculate attrition rate by category
def calc_attrition_by_category(df, column):
    attrition = df.groupby(column)['Attrition'].agg(['mean', 'count'])
    attrition['mean'] = attrition['mean'] * 100  # Convert to percentage
    attrition = attrition.sort_values('mean', ascending=False)
    return attrition

# Function to predict attrition risk
def predict_attrition_risk(df, model):
    if model is None:
        return df.copy()
    
   
    
    # Make a copy to avoid modifying the original dataframe
    df_pred = df.copy()
   
    
    # Get predictions
    try:
        # Predict probability of attrition (class 1)
        df_pred['AttritionProbability'] = model.predict_proba(df_pred)[:, 1]
        
        # Create risk categories
        df_pred['RiskCategory'] = pd.cut(
            df_pred['AttritionProbability'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['Low Risk', 'Medium Risk', 'High Risk']
        )
    except Exception as e:
        st.error(f"Error predicting attrition risk: {str(e)}")
        df_pred['AttritionProbability'] = 0
        df_pred['RiskCategory'] = 'Error'
    
    return df_pred

# Main function
def main():
    # Title
    st.title("Jaya Jaya Maju - Employee Attrition Dashboard")
    
    # Load and prepare data
    df = load_data()
    if df.empty:
        st.error("No data available. Please check the data source.")
        return
    
    df = create_age_groups(df)
    df = create_income_groups(df)
    
    # Load the machine learning model
    model = load_model()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Department filter
    departments = ["All"] + sorted(df['Department'].unique().tolist())
    selected_dept = st.sidebar.selectbox("Department", departments)
    
    # Job Role filter
    job_roles = ["All"] + sorted(df['JobRole'].unique().tolist())
    selected_role = st.sidebar.selectbox("Job Role", job_roles)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_dept != "All":
        filtered_df = filtered_df[filtered_df['Department'] == selected_dept]
    if selected_role != "All":
        filtered_df = filtered_df[filtered_df['JobRole'] == selected_role]
    
    # Calculate overall attrition rate for filtered data
    overall_attrition = filtered_df['Attrition'].mean() * 100
    
    # Overview metrics
    st.header("Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Employees", len(filtered_df))
    
    with col2:
        st.metric("Attrition Rate", f"{overall_attrition:.2f}%", 
                 delta=f"{overall_attrition - 10:.2f}%" if overall_attrition > 10 else None,
                 delta_color="inverse")
    
    with col3:
        overtime_pct = filtered_df[filtered_df['OverTime'] == 'Yes'].shape[0] / len(filtered_df) * 100
        st.metric("Employees Working Overtime", f"{overtime_pct:.2f}%")
    
    # Tabs for different analyses
    tab1, tab2 = st.tabs(["Attrition Factors", "ML Predictions"])
    
    with tab1:
        # Attrition by Key Factors
        st.subheader("Attrition by Key Factors")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Job Role and Attrition
            job_attrition = calc_attrition_by_category(filtered_df, 'JobRole')
            fig = px.bar(
                job_attrition.reset_index(), 
                x='JobRole', 
                y='mean',
                text='count',
                title='Attrition Rate by Job Role',
                labels={'mean': 'Attrition Rate (%)', 'JobRole': 'Job Role', 'count': 'Count'},
                color='mean',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Overtime and Attrition
            overtime_attrition = calc_attrition_by_category(filtered_df, 'OverTime')
            fig = px.bar(
                overtime_attrition.reset_index(), 
                x='OverTime', 
                y='mean',
                text='count',
                title='Attrition Rate by Overtime Status',
                labels={'mean': 'Attrition Rate (%)', 'OverTime': 'Overtime', 'count': 'Count'},
                color='mean',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Income Group and Attrition
            income_attrition = calc_attrition_by_category(filtered_df, 'IncomeGroup')
            fig = px.bar(
                income_attrition.reset_index(), 
                x='IncomeGroup', 
                y='mean',
                text='count',
                title='Attrition Rate by Income Group',
                labels={'mean': 'Attrition Rate (%)', 'IncomeGroup': 'Income Group', 'count': 'Count'},
                color='mean',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # Age Group and Attrition
            age_attrition = calc_attrition_by_category(filtered_df, 'AgeGroup')
            fig = px.bar(
                age_attrition.reset_index(), 
                x='AgeGroup', 
                y='mean',
                text='count',
                title='Attrition Rate by Age Group',
                labels={'mean': 'Attrition Rate (%)', 'AgeGroup': 'Age Group', 'count': 'Count'},
                color='mean',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Machine Learning Predictions
        st.subheader("Machine Learning Predictions")
        
        if model is not None:
            # Add ML predictions to the dataframe
            df_with_predictions = predict_attrition_risk(filtered_df, model)
            
            # Display model information
            st.info("This tab uses a Gradient Boosting machine learning model to predict employee attrition risk. The model was trained on historical employee data and has an accuracy of 85.85%.")
            
            # Show distribution of risk categories
            risk_counts = df_with_predictions['RiskCategory'].value_counts().reset_index()
            risk_counts.columns = ['Risk Category', 'Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart of risk categories
                fig = px.pie(
                    risk_counts, 
                    values='Count', 
                    names='Risk Category',
                    title='Employee Attrition Risk Distribution',
                    color='Risk Category',
                    color_discrete_map={
                        'Low Risk': '#66BB6A',
                        'Medium Risk': '#FFA726',
                        'High Risk': '#EF5350'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Histogram of attrition probabilities
                fig = px.histogram(
                    df_with_predictions, 
                    x='AttritionProbability',
                    nbins=20,
                    title='Distribution of Attrition Probabilities',
                    labels={'AttritionProbability': 'Probability of Leaving'},
                    color_discrete_sequence=['#1E88E5']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Display high risk employees
            high_risk = df_with_predictions[df_with_predictions['RiskCategory'] == 'High Risk']
            if not high_risk.empty:
                st.warning("⚠️ These employees are at high risk of attrition based on multiple factors")
                high_risk_display = high_risk[['EmployeeId', 'Department', 'JobRole', 'Age', 'JobSatisfaction', 'WorkLifeBalance', 'OverTime', 'MonthlyIncome']]
                st.dataframe(high_risk_display)
            else:
                st.success("No employees are currently at high risk of attrition in the selected filters.")
        else:
            st.error("Machine learning model could not be loaded. Please check the model file path.")
    
    # Recommendations
    st.header("Recommendations")
    
    st.markdown('''
    Based on the analysis, here are some recommendations to reduce attrition:
    
    1. **Address Overtime Issues**: Employees working overtime have nearly 3x higher attrition rates.
    2. **Improve Entry-Level Retention**: Level 1 employees have the highest attrition rates.
    3. **Review Compensation for Lower Income Groups**: Lower income groups show dramatically higher attrition.
    4. **Focus on Work-Life Balance**: Poor work-life balance correlates with higher attrition.
    5. **Target Support for High-Risk Roles**: Sales Representatives and Laboratory Technicians have the highest attrition.
    ''')

if __name__ == "__main__":
    main()
