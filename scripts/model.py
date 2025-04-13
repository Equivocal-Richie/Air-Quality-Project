import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Load feature-engineered data
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "..", "data", "processed", "featured_data.csv")
df = pd.read_csv(csv_path)

# Prepare data
X = df.drop(['aqi', 'timestamp', 'latitude', 'longitude', 'city', 'state', 'country', 'main_pollutant'], axis=1)
y = df['aqi']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Gradient Boosting with GridSearchCV
gb = GradientBoostingRegressor(random_state=42)
gb_params = {
    'n_estimators': [100, 200],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'subsample': [0.8, 1.0]
}
gb_grid = GridSearchCV(gb, gb_params, cv=5, scoring='neg_mean_absolute_error')
gb_grid.fit(X_train, y_train)
gb_best = gb_grid.best_estimator_
gb_predictions = gb_best.predict(X_test)
gb_cv_scores = cross_val_score(gb_best, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')

# Evaluation
def evaluate_model(predictions, y_test, model_name, cv_scores):
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    print(f"{model_name} MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.2f}, CV MAE: {np.mean(cv_scores):.2f}")

evaluate_model(gb_predictions, y_test, "Gradient Boosting", gb_cv_scores)

# Feature Importance Analysis
feature_importance = gb_best.feature_importances_
feature_names = X.columns
feature_importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': feature_importance})
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)
print(feature_importance_df)

# Save the best model
joblib.dump(gb_best, 'gb_best_model.joblib')