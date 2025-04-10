import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures

# Load cleaned data
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "..", "data", "processed", "cleaned_data.csv")
df = pd.read_csv(csv_path)

#-----1. Time-Based Features(Temporal Patterns)-----#
'''
Rationale: Air quality is highly dependent on time. 
We'll extract features that capture hourly, daily, weekly, and monthly trends.

Methods:
    Hour of the Day: Captures diurnal patterns (e.g., traffic rush hours).
    Day of the Week: Captures weekly patterns (e.g., weekday vs. weekend).
    Month of the Year: Captures seasonal variations.
    Time Since Last Peak: Captures how long it has been since a high pollution event.
'''
# Time-based features
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek  # Monday=0, Sunday=6
df['month'] = df['timestamp'].dt.month

# Time since last peak (example: AQI peak)
df = df.sort_values(by=['latitude', 'longitude', 'timestamp'])
df['time_since_last_peak'] = df.groupby(['latitude', 'longitude'])['aqi'].transform(lambda x: (x > x.quantile(0.95)).astype(int).cumsum())


#-----2. Location-Based Features (Spatial Patterns)-----#
'''
Rationale: Air quality varies significantly across locations. 
We'll capture spatial variations using latitude and longitude.

Methods:
    Distance from City Center: Measures proximity to urban areas.
    Latitude and Longitude as Features: Directly used to capture spatial coordinates.
'''
# Distance from city center (Using the first row as the city center)
city_center_lat = df['latitude'].iloc[0]
city_center_lon = df['longitude'].iloc[0]
df['distance_from_city_center'] = np.sqrt((df['latitude'] - city_center_lat)**2 + (df['longitude'] - city_center_lon)**2)


#-----3. Weather-Related Features (Meteorological Influence)-----#
'''
Rationale: Weather conditions significantly impact air quality. 
We'll capture these influences

Methods:
    Wind Components: Convert wind speed and direction into eastward and northward components.
    Wind Speed Magnitude: Direct wind speed.
    Humidity and Temperature Interaction: Captures the combined effect of humidity and temperature.
'''
# Wind components
df['wind_east'] = df['wind_speed'] * np.sin(np.radians(df['wind_direction']))
df['wind_north'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))

# Humidity and temperature interaction
df['humidity_temp_interaction'] = df['humidity'] * df['temperature']


#-----4. Air Quality Indices (Composite Measures)-----#
'''
Rationale: Combining multiple pollutants into a single index can provide a more holistic view of air quality.

Methods:
    Weighted AQI: Combine PM2.5 and PM10 using weights based on their relative importance.
'''
# Weighted AQI (Using equal weights)
df['weighted_aqi'] = 0.5 * df['pm25'] + 0.5 * df['pm10']


#-----5. Feature Scaling (Normalization/Standardization)-----#
'''
Rationale: Scaling ensures that features are on a similar scale, improving model performance.

Methods:
    StandardScaler: Standardizes features to have zero mean and unit variance.
'''
# Feature scaling
numerical_cols = df.select_dtypes(include=['number']).columns
scaler = StandardScaler()
df[numerical_cols] = scaler.fit_transform(df[numerical_cols])


#-----6. Feature Selection (Dimensionality Reduction -----#
'''
Rationale: Selecting the most relevant features can reduce noise and improve model interpretability.

Methods:
    Correlation Analysis: Remove highly correlated features.
    Tree-Based Feature Importance: Use tree-based models to rank feature importance.
'''
# Correlation analysis (Remove highly correlated features)
numeric_df = df.select_dtypes(include=['number'])  # Select only numeric columns
corr_matrix = numeric_df.corr()

upper = corr_matrix.abs().where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.9)]
df.drop(to_drop, axis=1, inplace=True)


#-----7. Interaction Features (Non-Linear Relationships) -----#
'''
Rationale: Captures non-linear relationships between features.

Methods:
    Polynomial Features: Create polynomial combinations of features.
'''
# Polynomial features (Degree 2)
poly = PolynomialFeatures(degree=2, interaction_only=True)
poly_features = poly.fit_transform(df[['hour', 'day_of_week', 'month']])
poly_feature_names = poly.get_feature_names_out(['hour', 'day_of_week', 'month'])
df[poly_feature_names[1:]] = poly_features[:, 1:] # Exclude the intercept term


#-----8. Save Feature-Engineered Data -----#
# Construct the path to save featured_data.csv
feature_csv_path = os.path.join(script_dir, "..", "data", "processed", "featured_data.csv")

# Save the data to a CSV file
df.to_csv(feature_csv_path, index=False)