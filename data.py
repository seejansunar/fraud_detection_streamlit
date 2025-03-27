import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import IsolationForest

faker = Faker()

# Global variable to store the Isolation Forest model
isolation_forest_model = None
preprocessor = None

def preprocess_data(df):
    """
    Preprocess the transaction data for Isolation Forest
    
    Args:
        df (pd.DataFrame): Input transaction dataframe
    
    Returns:
        np.ndarray: Preprocessed feature matrix
    """
    # Create a copy of the dataframe to avoid modifying the original
    df_copy = df.copy()
    
    # Convert timestamp to numeric feature (seconds since first timestamp)
    df_copy['timestamp_numeric'] = (df_copy['timestamp'] - df_copy['timestamp'].min()).dt.total_seconds()
    
    # Preprocessing pipeline
    global preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['amount', 'timestamp_numeric']),
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['purpose', 'country'])
        ])
    
    # Return preprocessed features
    return preprocessor.fit_transform(df_copy)

def train_isolation_forest(df, contamination=0.1):
    """
    Train Isolation Forest model on the transaction data
    
    Args:
        df (pd.DataFrame): Input transaction dataframe
        contamination (float): Expected proportion of outliers, defaults to 10%
    
    Returns:
        sklearn.ensemble.IsolationForest: Trained Isolation Forest model
    """
    # Preprocess the data
    X = preprocess_data(df)
    
    # Train Isolation Forest
    global isolation_forest_model
    isolation_forest_model = IsolationForest(
        contamination=contamination, 
        random_state=42
    )
    isolation_forest_model.fit(X)
    
    return isolation_forest_model

def detect_outliers(df):
    """
    Detect outliers in the transaction data
    
    Args:
        df (pd.DataFrame): Input transaction dataframe
    
    Returns:
        pd.DataFrame: DataFrame with added 'is_outlier' column
    """
    # If no model exists, train one
    global isolation_forest_model, preprocessor
    if isolation_forest_model is None or preprocessor is None:
        train_isolation_forest(df)
    
    # Preprocess the data
    X = preprocess_data(df)
    
    # Predict outliers (-1 for outliers, 1 for inliers)
    outlier_labels = isolation_forest_model.predict(X)
    
    # Create a copy of the dataframe and add outlier column
    df_with_outliers = df.copy()
    df_with_outliers['is_outlier'] = (outlier_labels == -1).astype(int)
    
    return df_with_outliers

def generate_transaction_row(
    timestamp: datetime,
    amount_min: float,
    amount_max: float,
    purposes: list,
    countries: list
):
    row = {
      "timestamp": timestamp,
      "amount": float("{0:.2f}".format(random.uniform(amount_min, amount_max))),
      "purpose": (
        random.choice(purposes)
        if purposes
        else random.choice(('Entertainment', 'Holiday', 'Transportation', 'Bills', 'Medical', 'Misc'))
      ),
      "country": random.choice(countries) if countries else faker.country_code('alpha-3')
    }
    return row

def generate_timeseries_data(num_rows: int, start_timestamp: datetime, **kwargs):
    data = []
    now = datetime.now()
    timestamp = start_timestamp or datetime.now()
    for _ in range(num_rows):
        timestamp += timedelta(seconds=random.randint(1, 3600))
        params = dict(timestamp=timestamp, **kwargs)
        data.append(generate_transaction_row(**params))
    
    # Convert to DataFrame and detect outliers
    df = pd.DataFrame(data)
    return detect_outliers(df)