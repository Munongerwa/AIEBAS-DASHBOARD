import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback
from flask import session
from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objs as go
import datetime

# Function to get user-specific database engine
def get_user_db_engine():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

layout = html.Div([
    html.H1([
        html.I(className="fas fa-shopping-cart me-2"),
        "Sales Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="sales-connection-status"),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-filter me-2"),
                        "Analysis Filters"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Select Year", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-3"
                                )
                            ], width=6),
                            
                            dbc.Col([
                                dbc.Label("Analysis Type", className="mb-2"),
                                dcc.Dropdown(
                                    id="sales-analysis-type",
                                    options=[
                                        {'label': 'Monthly Sales', 'value': 'monthly'},
                                        {'label': 'Quarterly Sales', 'value': 'quarterly'},
                                        {'label': 'Project Performance', 'value': 'product'}
                                    ],
                                    value='monthly',
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Analysis"
                        ], id="refresh-sales-button", color="primary", className="w-100")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Sales", className="card-title text-center"),
                            html.H2(id="total-sales", children="$0", className="text-center text-success fw-bold"),
                            html.P(id="sales-change", children="vs previous year", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Transactions", className="card-title text-center"),
                            html.H2(id="total-transactions", children="0", className="text-center text-primary fw-bold"),
                            html.P("Sales transactions", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Avg Transaction", className="card-title text-center"),
                            html.H2(id="avg-transaction", children="$0", className="text-center text-info fw-bold"),
                            html.P("Per sale", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=4)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Sales Trend Analysis"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="sales-trend-chart", style={"height": "600px"})
                    ])
                ], className="mb-4")
            ], width=20, md=10),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Sales Distribution"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="sales-distribution-chart", style={"height": "600px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6)
        ])
    ], className="mt-4", fluid=True)
])

# Main callback for sales analysis
@callback(
    [Output("sales-connection-status", "children"),
     Output("total-sales", "children"),
     Output("total-transactions", "children"),
     Output("avg-transaction", "children"),
     Output("sales-trend-chart", "figure"),
     Output("sales-distribution-chart", "figure")],
    [Input("refresh-sales-button", "n_clicks")],
    [Input("sales-year-dropdown", "value"),
     Input("sales-analysis-type", "value")],
    prevent_initial_call=False
)
def update_sales_analysis(n_clicks, selected_year, analysis_type):
    engine = get_user_db_engine()
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return [not_connected_alert, "$0", "0", "$0", empty_fig, empty_fig]
    
    try:
        current_year = selected_year
        previous_year = current_year - 1
        
        # Total Sales (Current Year)
        total_sales_query = f"""
        SELECT SUM(sale_value) AS total_sales FROM Stands WHERE YEAR(registration_date) = {current_year}
        """
        sales_df = pd.read_sql(total_sales_query, engine)
        current_total_sales = sales_df.iloc[0]['total_sales'] if not sales_df.empty and sales_df.iloc[0]['total_sales'] else 0
        formatted_total_sales = f"${current_total_sales:,.2f}" if current_total_sales else "$0"
        
        # Total Sales (Previous Year) for comparison
        total_sales_query_prev = f"""
        SELECT SUM(sale_value) AS total_sales FROM Stands WHERE YEAR(registration_date) = {previous_year}
        """
        sales_df_prev = pd.read_sql(total_sales_query_prev, engine)
        previous_total_sales = sales_df_prev.iloc[0]['total_sales'] if not sales_df_prev.empty and sales_df_prev.iloc[0]['total_sales'] else 0
        
        # Calculate sales change
        if previous_total_sales > 0:
            sales_change = ((current_total_sales - previous_total_sales) / previous_total_sales) * 100
            sales_change_text = f"{sales_change:+.1f}% vs {previous_year}"
        elif current_total_sales > 0 and previous_total_sales == 0:
            sales_change_text = f"+∞% vs {previous_year}"
        else:
            sales_change_text = "0% vs previous year"
        
        # Total Transactions (Current Year)
        total_transactions_query = f"""
        SELECT COUNT(stand_number) AS total_transactions FROM Stands WHERE YEAR(registration_date) = {current_year}
        """
        transactions_df = pd.read_sql(total_transactions_query, engine)
        current_total_transactions = transactions_df.iloc[0]['total_transactions'] if not transactions_df.empty and transactions_df.iloc[0]['total_transactions'] else 0
        
        # Total Transactions (Previous Year)
        total_transactions_query_prev = f"""
        SELECT COUNT(stand_number) AS total_transactions FROM Stands WHERE YEAR(registration_date) = {previous_year}
        """
        transactions_df_prev = pd.read_sql(total_transactions_query_prev, engine)
        previous_total_transactions = transactions_df_prev.iloc[0]['total_transactions'] if not transactions_df_prev.empty and transactions_df_prev.iloc[0]['total_transactions'] else 0
        
        # Average Transaction (Current Year)
        avg_transaction_query = f"""
        SELECT AVG(sale_value) AS avg_transaction FROM Stands WHERE YEAR(registration_date) = {current_year}
        """
        avg_df = pd.read_sql(avg_transaction_query, engine)
        current_avg_transaction = avg_df.iloc[0]['avg_transaction'] if not avg_df.empty and avg_df.iloc[0]['avg_transaction'] else 0
        formatted_avg_transaction = f"${current_avg_transaction:,.2f}" if current_avg_transaction else "$0"
        
        # Average Transaction (Previous Year)
        avg_transaction_query_prev = f"""
        SELECT AVG(sale_value) AS avg_transaction FROM Stands WHERE YEAR(registration_date) = {previous_year}
        """
        avg_df_prev = pd.read_sql(avg_transaction_query_prev, engine)
        previous_avg_transaction = avg_df_prev.iloc[0]['avg_transaction'] if not avg_df_prev.empty and avg_df_prev.iloc[0]['avg_transaction'] else 0
        
        # Calculate avg transaction change
        if previous_avg_transaction > 0:
            avg_change = ((current_avg_transaction - previous_avg_transaction) / previous_avg_transaction) * 100
            avg_change_text = f"Avg: {avg_change:+.1f}% vs {previous_year}"
        elif current_avg_transaction > 0 and previous_avg_transaction == 0:
            avg_change_text = f"Avg: +∞% vs {previous_year}"
        else:
            avg_change_text = "Avg: 0% vs previous year"
        
        # the sales change text including avg transaction info
        combined_change_text = f"{sales_change_text} | {avg_change_text}"
        
        # Sales Trend Analysis
        if analysis_type == 'monthly':
            trend_query = f"""
            SELECT 
                MONTH(registration_date) AS period,
                SUM(sale_value) AS total_sales,
                COUNT(stand_number) AS transaction_count
            FROM Stands 
            WHERE YEAR(registration_date) = {current_year}
            GROUP BY MONTH(registration_date)
            ORDER BY period
            """
            period_label = 'Month'
            period_names = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
        elif analysis_type == 'quarterly':
            trend_query = f"""
            SELECT 
                QUARTER(registration_date) AS period,
                SUM(sale_value) AS total_sales,
                COUNT(stand_number) AS transaction_count
            FROM Stands 
            WHERE YEAR(registration_date) = {current_year}
            GROUP BY QUARTER(registration_date)
            ORDER BY period
            """
            period_label = 'Quarter'
            period_names = [f"Q{i}" for i in range(1, 5)]
        else:  # project
            trend_query = f"""
            SELECT 
                project_id AS period,
                SUM(sale_value) AS total_sales,
                COUNT(stand_number) AS transaction_count
            FROM Stands 
            WHERE YEAR(registration_date) = {current_year}
            GROUP BY project_id
            ORDER BY total_sales DESC
            LIMIT 10
            """
            period_label = 'Project'
            period_names = []
        
        trend_df = pd.read_sql(trend_query, engine)
        
        if not trend_df.empty:
            if analysis_type == 'monthly':
                trend_df['period_name'] = trend_df['period'].apply(lambda x: period_names[x-1] if 1 <= x <= 12 else f"Month {x}")
            elif analysis_type == 'quarterly':
                trend_df['period_name'] = trend_df['period'].apply(lambda x: period_names[x-1] if 1 <= x <= 4 else f"Q{x}")
            else:
                trend_df['period_name'] = trend_df['period'].apply(lambda x: f"Project {x}")
            
            # Handling missing periods
            if analysis_type in ['monthly', 'quarterly']:
                existing_periods = trend_df['period'].tolist()
                missing_periods = []
                max_period = 12 if analysis_type == 'monthly' else 4
                for i in range(1, max_period + 1):
                    if i not in existing_periods:
                        missing_periods.append({
                            'period': i,
                            'total_sales': 0,
                            'transaction_count': 0,
                            'period_name': period_names[i-1] if analysis_type == 'monthly' else f"Q{i}"
                        })
                
                if missing_periods:
                    missing_df = pd.DataFrame(missing_periods)
                    trend_df = pd.concat([trend_df, missing_df], ignore_index=True)
                    trend_df.sort_values('period', inplace=True)
            
            # trend chart
            trend_fig = go.Figure()
            trend_fig.add_trace(go.Scatter(
                x=trend_df['period_name'],
                y=trend_df['total_sales'],
                mode='lines+markers',
                name='Sales Value',
                line=dict(color='#2c4bbc', width=3),
                marker=dict(size=8)
            ))
            trend_fig.add_trace(go.Bar(
                x=trend_df['period_name'],
                y=trend_df['transaction_count'],
                name='Transaction Count',
                yaxis='y2',
                opacity=0.6,
            ))
            trend_fig.update_layout(
                title=f'{period_label} Sales Trend Analysis',
                xaxis_title=period_label,
                yaxis_title='Sales Amount',
                yaxis2=dict(
                    title='Transaction Count',
                    overlaying='y',
                    side='right'
                ),
                template='plotly_white'
            )
        else:
            trend_fig = go.Figure()
            trend_fig.update_layout(title="No Data Available")
        
        #Sales Distribution (Pie Chart)
        distribution_query = f"""
        SELECT 
            project_id,
            SUM(sale_value) AS total_sales
        FROM Stands 
        WHERE YEAR(registration_date) = {current_year}
        GROUP BY project_id
        ORDER BY total_sales DESC
        """
        dist_df = pd.read_sql(distribution_query, engine)
        
        if not dist_df.empty:
            pie_fig = go.Figure(data=[go.Pie(
                labels=[f"Project {row['project_id']}" for _, row in dist_df.iterrows()],
                values=dist_df['total_sales'],
                hole=0.3
            )])
            pie_fig.update_layout(title="Sales Distribution by Project")
        else:
            pie_fig = go.Figure()
            pie_fig.update_layout(title="No Data Available")
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing {analysis_type} sales data for Year: {current_year}"
        ], color="success")
        
        return [status, formatted_total_sales, str(current_total_transactions), formatted_avg_transaction, trend_fig, pie_fig]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return [error_alert, "$0", "0", "$0", empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()