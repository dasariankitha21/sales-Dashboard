import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'sales_data.csv'

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=['date'])
    df['product'] = df['product'].astype(str)
    df['region'] = df['region'].astype(str)
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['average_price'] = df['revenue'] / df['sales']
    return df


df = load_data(DATA_PATH)

st.set_page_config(page_title='Sales & Revenue Dashboard', layout='wide')
st.title('Sales & Revenue Dashboard')
st.markdown('Explore total sales, revenue trends, top products, and regional performance with interactive filters.')

with st.sidebar:
    st.header('Filters')
    date_min, date_max = st.date_input(
        'Date range',
        value=[df['date'].min().date(), df['date'].max().date()],
        min_value=df['date'].min().date(),
        max_value=df['date'].max().date(),
    )
    product_filter = st.multiselect('Product', sorted(df['product'].unique()), default=sorted(df['product'].unique()))
    region_filter = st.multiselect('Region', sorted(df['region'].unique()), default=sorted(df['region'].unique()))
    show_raw = st.checkbox('Show raw data table', value=False)

filtered = df[
    (df['date'] >= pd.to_datetime(date_min)) &
    (df['date'] <= pd.to_datetime(date_max)) &
    (df['product'].isin(product_filter)) &
    (df['region'].isin(region_filter))
]

if filtered.empty:
    st.warning('No sales data matches the selected filters. Please adjust the date, product, or region.')
else:
    total_sales = filtered['sales'].sum()
    total_revenue = filtered['revenue'].sum()
    average_price = filtered['average_price'].mean()
    top_product = (
        filtered.groupby('product', as_index=False)['revenue']
        .sum()
        .sort_values('revenue', ascending=False)
        .iloc[0]
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total Sales', f'{total_sales:,.0f}')
    col2.metric('Total Revenue', f'${total_revenue:,.0f}')
    col3.metric('Average Revenue per Unit', f'${average_price:,.2f}')
    col4.metric('Top Product', f"{top_product['product']} (${top_product['revenue']:,.0f})")

    st.subheader('Revenue and Sales Trends')
    trend_df = filtered.groupby('date', as_index=False)[['sales', 'revenue']].sum()
    trend_fig = px.line(
        trend_df,
        x='date',
        y=['sales', 'revenue'],
        title='Sales and Revenue Over Time',
        labels={'value': 'Amount', 'date': 'Date', 'variable': 'Metric'},
    )
    st.plotly_chart(trend_fig, width='stretch')

    st.subheader('Top Performing Products')
    product_summary = (
        filtered.groupby('product', as_index=False)
        .agg({'sales': 'sum', 'revenue': 'sum'})
        .sort_values('revenue', ascending=False)
    )
    product_fig = px.bar(
        product_summary,
        x='product',
        y='revenue',
        title='Revenue by Product',
        text='revenue',
    )
    product_fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    st.plotly_chart(product_fig, width='stretch')

    st.subheader('Regional Sales Performance')
    region_summary = (
        filtered.groupby('region', as_index=False)
        .agg({'sales': 'sum', 'revenue': 'sum'})
        .sort_values('revenue', ascending=False)
    )
    region_fig = px.bar(
        region_summary,
        x='region',
        y='revenue',
        title='Revenue by Region',
        color='sales',
        labels={'revenue': 'Revenue', 'sales': 'Sales'},
        hover_data=['sales'],
    )
    st.plotly_chart(region_fig, width='stretch')

    st.subheader('Sales Data Table')
    if show_raw:
        st.dataframe(filtered.reset_index(drop=True))

    st.subheader('Summary by Product')
    st.dataframe(product_summary.assign(revenue=lambda x: x['revenue'].map('${:,.0f}'.format)))

