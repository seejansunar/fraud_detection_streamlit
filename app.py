import time
from faker.providers.address.en_GB import Provider as EnGbAddressProvider
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff

from data import *

st.set_page_config(layout="wide")
st.title("COMP 1831 - Transaction Generator with Anomaly Detection")

if "df" not in st.session_state:
    columns = [
      "timestamp",
      "amount",
      "purpose",
      "country",
      "is_outlier"
    ]
    st.session_state['df'] = pd.DataFrame(columns=columns)

def generate_clicked():
    data = generate_timeseries_data(
        num_rows=st.session_state.dp_rows,
        start_timestamp=st.session_state.get("last_tx_timestamp", None),
        amount_min=st.session_state.dp_amount_range[0],
        amount_max=st.session_state.dp_amount_range[1],
        purposes=st.session_state.dp_purposes,
        countries=st.session_state.dp_countries,
    )
    st.session_state.last_tx_timestamp = data.iloc[-1]["timestamp"]
    st.session_state.df = st.session_state.df.append(data, ignore_index=True)

def data_params_widget():
    st.subheader("Data Parameters")
    st.info("Use the form below to configure new data parameters.")
    st.slider(
        'Transaction range',
        0.0, 100_000.0, (5_000.0, 80_000.0),
        key="dp_amount_range"
    )
    st.multiselect(
        'Purposes',
        ('Entertainment', 'Holiday', 'Transportation', 'Bills', 'Medical', 'Misc'),
        key="dp_purposes"
    )
    st.multiselect(
        'Countries',
        EnGbAddressProvider.alpha_3_country_codes,
        key="dp_countries"
    )

    st.number_input('Rows', min_value=1, step=1, key="dp_rows")

    st.button('Generate', on_click=generate_clicked)

def choropleth_widget():
    from urllib.request import urlopen
    import json
    with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
        counties = json.load(response)

    # Group by country with total count and outlier count
    data = st.session_state.df.groupby("country").agg({
        "country": "count", 
        "is_outlier": "sum"
    }).reset_index()
    data.columns = ["country", "total_count", "outlier_count"]

    # Create choropleth map
    fig = go.Figure(
        px.choropleth(
            data,
            geojson=counties,
            locations='country',
            color='outlier_count',
            color_continuous_scale="hot_r",
            hover_data=['total_count', 'outlier_count'],
        )
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=6.6,
        mapbox_center={"lat": 46.8, "lon": 8.2},
        title="Outliers by Country"
    )
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

def charts_widget():
    # Purpose distribution of outliers
    outlier_data = st.session_state.df[st.session_state.df['is_outlier'] == 1]
    total_data = st.session_state.df.groupby("purpose").size().reset_index(name="total_count")
    outlier_purpose_count = outlier_data.groupby("purpose").size().reset_index(name="outlier_count")
    
    # Merge total and outlier counts
    data = total_data.merge(outlier_purpose_count, on="purpose", how="left")
    data['outlier_count'] = data['outlier_count'].fillna(0)

    col1, col2 = st.columns([1, 1])
    with col1:
        # Bar chart of total transactions by purpose with outlier overlay
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data["purpose"],
            y=data["total_count"],
            name="Total Transactions",
            marker_color='blue'
        ))
        fig.add_trace(go.Bar(
            x=data["purpose"],
            y=data["outlier_count"],
            name="Outliers",
            marker_color='red'
        ))
        fig.update_layout(
            title="Transactions and Outliers by Purpose",
            xaxis_title="Purpose",
            yaxis_title="Count",
            barmode='overlay'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Line chart of transaction amounts, highlighting outliers
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=st.session_state.df["timestamp"], 
            y=st.session_state.df["amount"],
            mode='markers',
            name='Normal Transactions',
            marker=dict(color='blue', size=5)
        ))
        outliers = st.session_state.df[st.session_state.df['is_outlier'] == 1]
        fig.add_trace(go.Scatter(
            x=outliers["timestamp"], 
            y=outliers["amount"],
            mode='markers',
            name='Outliers',
            marker=dict(color='red', size=10, symbol='cross')
        ))
        fig.update_layout(
            title="Transaction Amounts Over Time",
            xaxis_title="Timestamp",
            yaxis_title="Amount"
        )
        st.plotly_chart(fig, use_container_width=True)

def metrics_widget():
    st.subheader("Transaction Metrics")
    col1, col2, col3 = st.columns(3)
    last_tx_count = st.session_state.get("last_tx_count", 0)
    
    with col1:
        st.metric(
            "Total Transactions",
            len(st.session_state.df),
            delta=len(st.session_state.df)-last_tx_count,
            delta_color="normal",
            help="Number of total transactions"
        )
    
    with col2:
        suspicious_count = st.session_state.df['is_outlier'].sum()
        st.metric(
            "Suspicious Transactions",
            suspicious_count,
            help="Number of suspicious (outlier) transactions detected by Isolation Forest"
        )
    
    with col3:
        outlier_percentage = (st.session_state.df['is_outlier'].sum() / len(st.session_state.df)) * 100 if len(st.session_state.df) > 0 else 0
        st.metric(
            "Outlier Percentage",
            f"{outlier_percentage:.2f}%",
            help="Percentage of transactions identified as outliers"
        )
    
    st.session_state.last_tx_count = len(st.session_state.df)

def general_widget():
    st.subheader("General")
    st.button('Clear state', on_click=lambda: st.session_state.clear())

def data_table_widget():
    st.markdown('# Generated data:')
    st.markdown('The dataframe below holds the data generated so far:')
    # Highlight outliers in the table
    styled_df = st.session_state.df.style.apply(
        lambda x: ['background-color: lightcoral' if val == 1 else '' for val in x],
        subset=['is_outlier']
    )
    st.dataframe(styled_df)

with st.sidebar:
    st.title("Configuration")
    data_params_widget()
    general_widget()

metrics_widget()
choropleth_widget()
charts_widget()
data_table_widget()