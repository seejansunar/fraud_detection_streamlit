
import time
from faker.providers.address.en_GB import Provider as EnGbAddressProvider
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff


from data import *

st.set_page_config(layout="wide")
st.title("COMP 1831 - Transaction Generator")

if "df" not in st.session_state:
    columns = [
      "timestamp",
      "amount",
      "purpose",
      "country"
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

  data = st.session_state.df.groupby("country").size().reset_index(name="count")
  fig = go.Figure(
      px.choropleth(
        data,
        geojson=counties,
        locations='country',
        color='count',
        color_continuous_scale="hot_r",
        range_color=(0, data["count"].max()),
      )
  )
  fig.update_layout(
      mapbox_style="carto-positron",
      mapbox_zoom=6.6,
      mapbox_center={"lat": 46.8, "lon": 8.2},
  )
  fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
  st.plotly_chart(fig, use_container_width=True)

def charts_widget():
  data = st.session_state.df.groupby("purpose").size().reset_index(name="count")
  col1, col2 = st.columns([1, 1])
  with col1:
    fig = px.bar(
        data,
        x="purpose",
        y="count",
        color="purpose",
        text="count",
    )
    st.plotly_chart(fig, use_container_width=True)
  with col2:
    fig = px.line(st.session_state.df,
    x = "timestamp", y = "amount",)
    st.plotly_chart(fig, use_container_width=True)

def metrics_widget():
  st.subheader("Transaction Metrics")
  col1, col2 = st.columns(2)
  last_tx_count = st.session_state.get("last_tx_count", 0)
  with col1:
    st.metric(
      "Total",
      len(st.session_state.df),
      delta=len(st.session_state.df)-last_tx_count,
      delta_color="normal",
      help="Number of total transactions"
    )
  with col2:
    st.metric(
      "Suspicious",
      0,
      help="Number of sucpicious transactions"
  )
  st.session_state.last_tx_count = len(st.session_state.df)


def general_widget():
  st.subheader("General")
  st.button('Clear state', on_click=lambda: st.session_state.clear() , )

def data_table_widget():
  st.markdown('# Generated data:')
  st.markdown('The dataframe below holds the data generated so far:')
  st.session_state.table = st.table(st.session_state.df)

with st.sidebar:
  st.title("Configuration")
  data_params_widget()
  general_widget()

metrics_widget()
choropleth_widget()
charts_widget()
