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
        html.I(className="fas fa-chart-line me-2"),
        "Dashboard"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="dashboard-connection-status"),
    
    # Filters Section with Year Selection
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-filter me-2"),
                        "Filters"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label([
                                    html.I(className="fas fa-calendar-alt me-1"),
                                    "Select Year"
                                ], className="mb-2"),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Data"
                        ], id="refresh-dashboard-button", color="primary", className="w-50")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Metrics Cards with YoY Comparisons
        dbc.Row([
            # Total Stand Value Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-dollar-sign fa-2x text-success"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Stand Value", className="card-title text-center"),
                            html.H2(id="total-stand-value", children="$0", className="text-center text-success fw-bold"),
                            html.P(id="stand-value-period", children="Year: --", className="text-center text-muted small"),
                            html.Div(id="stand-value-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=3),
            
            # Number of Stands Sold Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-house fa-2x text-primary"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Stands Sold", className="card-title text-center"),
                            html.H2(id="stands-sold-value", children="0", className="text-center text-primary fw-bold"),
                            html.P(id="stands-sold-period", children="Year: --", className="text-center text-muted small"),
                            html.Div(id="stands-sold-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=3),
            
            # Total Deposit Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-money-bill-wave fa-2x text-info"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Deposit", className="card-title text-center"),
                            html.H2(id="total-deposit-value", children="$0", className="text-center text-info fw-bold"),
                            html.P(id="deposit-period", children="Year: --", className="text-center text-muted small"),
                            html.Div(id="deposit-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=3),
            
            # Total Installment Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-file-invoice-dollar fa-2x text-warning"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Total Installment", className="card-title text-center"),
                            html.H2(id="total-installment-value", children="$0", className="text-center text-warning fw-bold"),
                            html.P(id="installment-period", children="Year: --", className="text-center text-muted small"),
                            html.Div(id="installment-yoy", className="text-center mt-2")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=3),
        ], className="mb-4"),
        
        # New Graphs Section (Pie Chart and Area Chart)
        dbc.Row([
            # Pie Chart and Area Chart Container
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Pie Chart Column
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-chart-pie me-2"),
                                        "Deposits vs Installments"
                                    ]),
                                    dbc.CardBody([
                                        dcc.Graph(id="deposits-installments-pie", style={"height": "400px"})
                                    ])
                                ])
                            ], width=12, md=6),
                            
                            # Area Chart Column
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-chart-area me-2"),
                                        "Stands Sold Over the Years"
                                    ]),
                                    dbc.CardBody([
                                        dcc.Graph(id="stands-sold-area", style={"height": "400px"})
                                    ])
                                ])
                            ], width=12, md=6)
                        ])
                    ])
                ], className="mb-4")
            ], width=12)
        ])
    ], className="mt-4", fluid=True)
])

# Dashboard callback with year-based queries, new graphs, and YoY comparisons
@callback(
    [Output("dashboard-connection-status", "children"),
     Output("total-stand-value", "children"),
     Output("stands-sold-value", "children"),
     Output("total-deposit-value", "children"),
     Output("total-installment-value", "children"),
     Output("stand-value-period", "children"),
     Output("stands-sold-period", "children"),
     Output("deposit-period", "children"),
     Output("installment-period", "children"),
     Output("deposits-installments-pie", "figure"),
     Output("stands-sold-area", "figure"),
     Output("stand-value-yoy", "children"),
     Output("stands-sold-yoy", "children"),
     Output("deposit-yoy", "children"),
     Output("installment-yoy", "children")],
    [Input("refresh-dashboard-button", "n_clicks")],
    [Input("year-dropdown", "value")],
    prevent_initial_call=False
)
def update_dashboard_metrics(n_clicks, selected_year):
    engine = get_user_db_engine()
    
    if not engine:
        # Return default values when not connected
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        # Empty figures
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        # Default YoY comparison values
        default_yoy = html.Span([
            html.I(className="fas fa-minus-circle me-1 text-muted"),
            "N/A"
        ], className="text-muted small")
        
        return [not_connected_alert, "$0", "0", "$0", "$0", "None", 
                "Year: --", "Year: --", "Year: --", "Year: --", "$0", "--",
                empty_fig, empty_fig,
                default_yoy, default_yoy, default_yoy, default_yoy]
    
    try:
        current_year = selected_year
        previous_year = current_year - 1
        
        # Query 1: Total Stand Value for current and previous year
        try:
            total_stand_value_query = """
            SELECT 
                YEAR(registration_date) AS year,
                SUM(sale_value) AS total_sale_value 
            FROM Stands 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            stand_value_df = pd.read_sql(total_stand_value_query, engine, params=(current_year, previous_year))
            
            current_stand_value = 0
            previous_stand_value = 0
            
            for _, row in stand_value_df.iterrows():
                if row['year'] == current_year:
                    current_stand_value = row['total_sale_value'] if row['total_sale_value'] else 0
                elif row['year'] == previous_year:
                    previous_stand_value = row['total_sale_value'] if row['total_sale_value'] else 0
                    
        except Exception as e:
            current_stand_value = 0
            previous_stand_value = 0
        
        formatted_stand_value = f"${current_stand_value:,.2f}" if current_stand_value else "$0"
        
        # Query 2: Number of Stands Sold for current and previous year
        try:
            stands_sold_query = """
            SELECT 
                YEAR(registration_date) AS year,
                COUNT(stand_number) AS total_stands_sold 
            FROM Stands 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            stands_sold_df = pd.read_sql(stands_sold_query, engine, params=(current_year, previous_year))
            
            current_stands_sold = 0
            previous_stands_sold = 0
            
            for _, row in stands_sold_df.iterrows():
                if row['year'] == current_year:
                    current_stands_sold = row['total_stands_sold'] if row['total_stands_sold'] else 0
                elif row['year'] == previous_year:
                    previous_stands_sold = row['total_stands_sold'] if row['total_stands_sold'] else 0
                    
        except Exception as e:
            current_stands_sold = 0
            previous_stands_sold = 0
        
        formatted_stands_sold = str(current_stands_sold) if current_stands_sold else "0"
        
        # Query 3: Total Deposit for current and previous year
        try:
            total_deposit_query = """
            SELECT 
                YEAR(registration_date) AS year,
                SUM(deposit_amount) AS total_deposit 
            FROM customer_accounts 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            deposit_df = pd.read_sql(total_deposit_query, engine, params=(current_year, previous_year))
            
            current_deposit = 0
            previous_deposit = 0
            
            for _, row in deposit_df.iterrows():
                if row['year'] == current_year:
                    current_deposit = row['total_deposit'] if row['total_deposit'] else 0
                elif row['year'] == previous_year:
                    previous_deposit = row['total_deposit'] if row['total_deposit'] else 0
                    
        except Exception as e:
            current_deposit = 0
            previous_deposit = 0
        
        formatted_deposit = f"${current_deposit:,.2f}" if current_deposit else "$0"
        
        # Query 4: Total Installment for current and previous year
        try:
            total_installment_query = """
            SELECT 
                YEAR(transaction_date) AS year,
                SUM(amount) AS total_installment 
            FROM customer_account_invoices
            WHERE YEAR(transaction_date) IN (%s, %s) AND description = 'Instalment'
            GROUP BY YEAR(transaction_date)
            """
            installment_df = pd.read_sql(total_installment_query, engine, params=(current_year, previous_year))
            
            current_installment = 0
            previous_installment = 0
            
            for _, row in installment_df.iterrows():
                if row['year'] == current_year:
                    current_installment = row['total_installment'] if row['total_installment'] else 0
                elif row['year'] == previous_year:
                    previous_installment = row['total_installment'] if row['total_installment'] else 0
                    
        except Exception as e:
            # Try without description filter
            try:
                total_installment_query = """
                SELECT 
                    YEAR(transaction_date) AS year,
                    SUM(amount) AS total_installment 
                FROM customer_account_invoices
                WHERE YEAR(transaction_date) IN (%s, %s)
                GROUP BY YEAR(transaction_date)
                """
                installment_df = pd.read_sql(total_installment_query, engine, params=(current_year, previous_year))
                
                current_installment = 0
                previous_installment = 0
                
                for _, row in installment_df.iterrows():
                    if row['year'] == current_year:
                        current_installment = row['total_installment'] if row['total_installment'] else 0
                    elif row['year'] == previous_year:
                        previous_installment = row['total_installment'] if row['total_installment'] else 0
            except:
                current_installment = 0
                previous_installment = 0
        
        formatted_installment = f"${current_installment:,.2f}" if current_installment else "$0"
        
        # Format period text
        period_text = f"Year: {current_year}"
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing data for Year: {current_year}"
        ], color="success")
        
        # YoY Comparison Calculations
        def calculate_yoy_change(current, previous):
            if previous == 0:
                if current == 0:
                    return html.Span([
                        html.I(className="fas fa-minus-circle me-1 text-muted"),
                        "0% (No change)"
                    ], className="text-muted small")
                else:
                    return html.Span([
                        html.I(className="fas fa-arrow-up me-1 text-success"),
                        f"+∞% (Prev: $0)"
                    ], className="text-success small")
            else:
                change = ((current - previous) / previous) * 100
                if change > 0:
                    icon_class = "fas fa-arrow-up me-1 text-success"
                    text_class = "text-success small"
                elif change < 0:
                    icon_class = "fas fa-arrow-down me-1 text-danger"
                    text_class = "text-danger small"
                else:
                    icon_class = "fas fa-minus-circle me-1 text-muted"
                    text_class = "text-muted small"
                
                return html.Span([
                    html.I(className=icon_class),
                    f"{change:+.1f}% (Prev: ${previous:,.0f})"
                ], className=text_class)
        
        # Calculate YoY changes
        stand_value_yoy = calculate_yoy_change(current_stand_value, previous_stand_value)
        stands_sold_yoy = calculate_yoy_change(current_stands_sold, previous_stands_sold)
        deposit_yoy = calculate_yoy_change(current_deposit, previous_deposit)
        installment_yoy = calculate_yoy_change(current_installment, previous_installment)
        
        # NEW GRAPHS SECTION
        
        # Pie Chart: Deposits vs Installments for selected year
        pie_data = [current_deposit, current_installment]
        pie_labels = ["Deposits", "Installments"]
        pie_colors = ["#ffcc00", '#2c4bbc']
        
        if sum(pie_data) > 0:
            pie_fig = go.Figure(data=[go.Pie(
                labels=pie_labels, 
                values=pie_data, 
                hole=.3, 
                marker=dict(colors=pie_colors)
            )])
            pie_fig.update_layout(
                title_text='Deposits vs Installments',
                height=400
            )
        else:
            pie_fig = go.Figure()
            pie_fig.update_layout(
                title="No Data Available for Deposits and Installments",
                height=400
            )
        
        # Area Chart: Stands Sold Over the Years (last 5 years)
        try:
            # Get data for the last 5 years including current year
            start_year = current_year - 4  # Last 5 years
            
            number_of_stands_query = """
            SELECT 
                YEAR(registration_date) AS year,
                COUNT(stand_number) AS total_stands_sold 
            FROM Stands 
            WHERE YEAR(registration_date) >= %s
            GROUP BY YEAR(registration_date)
            ORDER BY year
            """
            number_of_stands_df = pd.read_sql(number_of_stands_query, engine, params=(start_year,))
            
            if not number_of_stands_df.empty:
                # Ensure all years are present
                all_years = list(range(start_year, current_year + 1))
                existing_years = number_of_stands_df['year'].tolist()
                
                # Add missing years with 0 stands sold
                missing_years = []
                for year in all_years:
                    if year not in existing_years:
                        missing_years.append({'year': year, 'total_stands_sold': 0})
                
                if missing_years:
                    missing_df = pd.DataFrame(missing_years)
                    number_of_stands_df = pd.concat([number_of_stands_df, missing_df], ignore_index=True)
                    number_of_stands_df.sort_values('year', inplace=True)
                
                area_fig = go.Figure()
                area_fig.add_trace(go.Scatter(
                    x=number_of_stands_df['year'],
                    y=number_of_stands_df['total_stands_sold'],
                    mode='lines+markers',
                    fill='tozeroy',  # Fill the area under the line
                    name='Total Stands Sold',
                    line=dict(color="#ffcc00")
                ))
                area_fig.update_layout(
                    title='Total Stands Sold Over the Years',
                    xaxis_title='Year',
                    yaxis_title='Number of Stands Sold',
                    template='plotly_white',
                    height=400
                )
            else:
                # Create empty chart with all years
                all_years = list(range(start_year, current_year + 1))
                empty_data = {'year': all_years, 'total_stands_sold': [0] * len(all_years)}
                empty_df = pd.DataFrame(empty_data)
                
                area_fig = go.Figure()
                area_fig.add_trace(go.Scatter(
                    x=empty_df['year'],
                    y=empty_df['total_stands_sold'],
                    mode='lines+markers',
                    fill='tozeroy',
                    name='Total Stands Sold',
                    line=dict(color="#ffcc00")
                ))
                area_fig.update_layout(
                    title='Total Stands Sold Over the Years',
                    xaxis_title='Year',
                    yaxis_title='Number of Stands Sold',
                    template='plotly_white',
                    height=400
                )
        except Exception as e:
            # Handle error gracefully
            area_fig = go.Figure()
            area_fig.update_layout(
                title='Total Stands Sold Over the Years',
                xaxis_title='Year',
                yaxis_title='Number of Stands Sold',
                template='plotly_white',
                height=400
            )

        return [status, formatted_stand_value, formatted_stands_sold, formatted_deposit, 
                formatted_installment,  period_text, period_text,
                period_text, str(current_year),
                pie_fig, area_fig,
                stand_value_yoy, stands_sold_yoy, deposit_yoy, installment_yoy]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        period_text = f"Year: {selected_year}" if selected_year else "Year: --"
        
        # Empty figures for error case
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        # Default YoY comparison values
        default_yoy = html.Span([
            html.I(className="fas fa-minus-circle me-1 text-muted"),
            "N/A"
        ], className="text-muted small")
        
        return [error_alert, "$0", "0", "$0", "$0", "None", 
                period_text, period_text, period_text, period_text, "$0", "--" if not selected_year else str(selected_year),
                empty_fig, empty_fig,
                default_yoy, default_yoy, default_yoy, default_yoy]
    finally:
        if engine:
            engine.dispose()