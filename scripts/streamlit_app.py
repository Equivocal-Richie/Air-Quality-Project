import streamlit as st
import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

def main():
    try:
        # Load data and model
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "..", "data", "processed", "featured_data.csv")
        print(f"Loading data from: {csv_path}")
        df = pd.read_csv(csv_path)
        print(df.columns)
        model = joblib.load('gb_best_model.joblib')

        # Get the features the model was trained on
        model_features = model.feature_names_in_.tolist()

        # Streamlit app layout
        st.title("Air Quality Prediction App")

        # Sidebar for interactive controls
        st.sidebar.header("Input Features")
        hour = st.sidebar.slider("Hour of the Day", 0, 23, 12)
        day_of_week = st.sidebar.slider("Day of the Week (0=Monday, 6=Sunday)", 0, 6, 3)
        month = st.sidebar.slider("Month", 1, 12, 7)
        wind_speed = st.sidebar.slider("Wind Speed", float(df['wind_speed'].min()), float(df['wind_speed'].max()), float(df['wind_speed'].mean()))
        wind_direction = st.sidebar.slider("Wind Direction", float(df['wind_direction'].min()), float(df['wind_direction'].max()), float(df['wind_direction'].mean()))
        humidity = st.sidebar.slider("Humidity", float(df['humidity'].min()), float(df['humidity'].max()), float(df['humidity'].mean()))
        temperature = st.sidebar.slider("Temperature", float(df['temperature'].min()), float(df['temperature'].max()), float(df['temperature'].mean()))
        pressure = st.sidebar.slider("Pressure", float(df['pressure'].min()), float(df['pressure'].max()), float(df['pressure'].mean()))
        wind_east = st.sidebar.slider("Wind East Component", float(df['wind_east'].min()), float(df['wind_east'].max()), float(df['wind_east'].mean()))
        wind_north = st.sidebar.slider("Wind North Component", float(df['wind_north'].min()), float(df['wind_north'].max()), float(df['wind_north'].mean()))
        humidity_temp_interaction = st.sidebar.slider("Humidity Temp Interaction", float(df['humidity_temp_interaction'].min()), float(df['humidity_temp_interaction'].max()), float(df['humidity_temp_interaction'].mean()))

        # Default values for missing features
        pm25_mean = df['pm25'].mean()
        time_since_last_peak_mean = df['time_since_last_peak'].mean()
        hour_day_of_week_mean = df['hour day_of_week'].mean()
        hour_month_mean = df['hour month'].mean()
        day_of_week_month_mean = df['day_of_week month'].mean()

        # Create input_data DataFrame with all features
        input_data = pd.DataFrame([[hour, day_of_week, month, wind_speed, wind_direction, humidity, temperature, pressure, wind_east, wind_north, humidity_temp_interaction, pm25_mean, time_since_last_peak_mean, hour_day_of_week_mean, hour_month_mean, day_of_week_month_mean]],
                                  columns=['hour', 'day_of_week', 'month', 'wind_speed', 'wind_direction', 'humidity', 'temperature', 'pressure', 'wind_east', 'wind_north', 'humidity_temp_interaction', 'pm25', 'time_since_last_peak', 'hour day_of_week', 'hour month', 'day_of_week month'])

        # Scale the data
        numerical_cols = input_data.select_dtypes(include=['number']).columns
        scaler = StandardScaler()
        input_data[numerical_cols] = scaler.fit_transform(input_data[numerical_cols])

        # Select only the features the model was trained on
        input_data = input_data[model_features]

        # Prediction
        prediction = model.predict(input_data)

        # Main content area
        col1, col2 = st.columns(2)  # Divide into two columns

        with col1:
            st.subheader("Predicted AQI")
            st.write(f"Predicted AQI: {prediction[0]:.2f}")

        with col2:
            # Data visualizations
            st.subheader("AQI Distribution")
            fig_hist, ax_hist = plt.subplots()
            ax_hist.hist(df['aqi'])
            ax_hist.set_xlabel("AQI Value")  # Add x-axis label
            ax_hist.set_ylabel("Frequency")  # Add y-axis label
            st.pyplot(fig_hist)

            st.subheader("Feature Correlations")
            numeric_df = df.select_dtypes(include=['number'])
            fig_corr, ax_corr = plt.subplots()
            ax_corr.matshow(numeric_df.corr())
            ax_corr.set_xticks(range(len(numeric_df.columns)))  # Add x-axis ticks
            ax_corr.set_xticklabels(numeric_df.columns, rotation=90)  # Add x-axis labels
            ax_corr.set_yticks(range(len(numeric_df.columns)))  # Add y-axis ticks
            ax_corr.set_yticklabels(numeric_df.columns)  # Add y-axis labels
            st.pyplot(fig_corr)

    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()