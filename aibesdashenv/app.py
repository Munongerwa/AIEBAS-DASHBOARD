import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
from apps import home, dashboard, db_connection
import datetime
from flask import session
import uuid
import mysql.connector
from mysql.connector import Error
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True)
#server-side session support
app.server.secret_key = 'ettrde'  
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Location(id='redirect-url', refresh=False),
    dcc.Store(id='session-id'),  #this is for multi-user session management
    
    dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/aibes.png", style={"width": "5.9rem", 'margin-right': '200px', 'margin-left': '0px'}),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink([html.I(className="fas fa-home me-2"), "Home"], href="/", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-dashboard me-2"), "Dashboard"], href="/apps/dashboard", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Data Analysis"], href="/apps/data", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-info-circle me-2"), "About"], href="/apps/about", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-sign-in-alt me-2"), "Login"], href="/apps/db_connection", active="exact", id="login-nav-link"),
                        dbc.NavLink([html.I(className="fas fa-sign-out-alt me-2"), "Logout"], href="/apps/logout", active="exact", id="logout-nav-link"),
                    ],
                    className="me-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
            
            html.Div(id="navbar-connection-status", className="d-flex align-items-center ms-3"),
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    ),
    html.Div(id='page-content', children=[]),
])
# Session initialization callback
@app.callback(Output('session-id', 'data'),
              Input('url', 'pathname'))
def initialize_session(pathname):
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['db_config'] = None  # Store connection config instead of connection object
    return session['user_id']

@app.callback([Output('page-content', 'children'),
               Output('redirect-url', 'pathname'),
               Output('navbar-connection-status', 'children')],
              [Input('url', 'pathname'),
               Input('session-id', 'data')])
def display_page(pathname, session_id):
    # connection status for navbar
    connection_status = get_connection_status_component()  
    if pathname == '/apps/logout':
        # Clear user session
        session.pop('db_config', None)
        return [html.Div([
            dbc.Container([
                dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "You have been logged out successfully!"
                ], color="success", className="mt-5 text-center"),
                dbc.Button([
                    html.I(className="fas fa-sign-in-alt me-2"),
                    "Login Again"
                ], href="/apps/db_connection", color="primary", className="mt-3")
            ], className="text-center")
        ]), dash.no_update, connection_status]
    
    if pathname == '/apps/dashboard':
        if not get_user_db_connection():
            # Show error on dashboard page
            error_page = html.Div([
                dbc.Container([
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Database connection required! Please connect to database first."
                    ], color="warning", className="mt-5 text-center"),
                    dbc.Button([
                        html.I(className="fas fa-database me-2"),
                        "Go to Connection Page"
                    ], href="/apps/db_connection", color="primary", className="mt-3")
                ], className="text-center")
            ])
            return [error_page, dash.no_update, connection_status]
    
    if pathname == '/apps/db_connection':
        if get_user_db_connection():
            # Show already connected message
            already_connected_page = html.Div([
                dbc.Container([
                    dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        "You are already connected to the database!"
                    ], color="success", className="mt-5 text-center"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-dashboard me-2"),
                                "Go to Dashboard"
                            ], href="/apps/dashboard", color="primary", className="me-2")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-home me-2"),
                                "Go to Home"
                            ], href="/", color="secondary")
                        ], width="auto")
                    ], className="justify-content-center mt-3")
                ], className="text-center")
            ])
            return [already_connected_page, dash.no_update, connection_status]
    
    #page routing
    if pathname == '/':
        return [home.layout, dash.no_update, connection_status]
    elif pathname == '/apps/db_connection':
        return [db_connection.layout, dash.no_update, connection_status]
    elif pathname == '/apps/dashboard':
        return [dashboard.layout, dash.no_update, connection_status]
    elif pathname == '/apps/about':
        return [html.Div([html.H1("About Page")]), dash.no_update, connection_status]
    elif pathname == '/apps/data':
        return [html.Div([html.H1("Data Page")]), dash.no_update, connection_status]

    else:
        not_found = dbc.Container([
            html.H1("404 - Page not found"),
            html.P("The requested page does not exist.")
        ])
        return [not_found, dash.no_update, connection_status]

# Callback for navbar toggle
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    prevent_initial_call=False
)
def toggle_navbar_collapse(n):
    if n:
        return False
    return True

# Dashboard callback
@app.callback(
    [Output("dashboard-connection-status", "children"),
     Output("total-stand-value", "children"),
     Output("stands-sold-value", "children"),
     Output("total-deposit-value", "children"),
     Output("total-installment-value", "children"),
     Output("top-project-value", "children"),
     Output("stand-value-period", "children"),
     Output("stands-sold-period", "children"),
     Output("deposit-period", "children"),
     Output("installment-period", "children"),
     Output("top-project-amount", "children"),
     Output("selected-year-info", "children"),
     Output("deposits-installments-pie", "figure"),
     Output("stands-sold-area", "figure"),
     Output("stand-value-yoy", "children"),
     Output("stands-sold-yoy", "children"),
     Output("deposit-yoy", "children"),
     Output("installment-yoy", "children")],
    [Input("refresh-dashboard-button", "n_clicks")],
    [State("year-dropdown", "value")],
    prevent_initial_call=False
)
def update_dashboard_metrics(n_clicks, selected_year):
    user_db_conn = get_user_db_connection()
    
    if not user_db_conn:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        # Empty figures
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
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
        
        # Total Stand Value for current and previous year
        try:
            total_stand_value_query = """
            SELECT 
                YEAR(registration_date) AS year,
                SUM(sale_value) AS total_sale_value 
            FROM Stands 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            stand_value_df = pd.read_sql(total_stand_value_query, user_db_conn, params=(current_year, previous_year))
            
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
        
        #Number of Stands Sold for current and previous year
        try:
            stands_sold_query = """
            SELECT 
                YEAR(registration_date) AS year,
                COUNT(stand_number) AS total_stands_sold 
            FROM Stands 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            stands_sold_df = pd.read_sql(stands_sold_query, user_db_conn, params=(current_year, previous_year))
            
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
        
        #Total Deposit for current and previous year
        try:
            total_deposit_query = """
            SELECT 
                YEAR(registration_date) AS year,
                SUM(deposit_amount) AS total_deposit 
            FROM customer_accounts 
            WHERE YEAR(registration_date) IN (%s, %s)
            GROUP BY YEAR(registration_date)
            """
            deposit_df = pd.read_sql(total_deposit_query, user_db_conn, params=(current_year, previous_year))
            
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
        
        #Total Installment for current and previous year
        try:
            total_installment_query = """
            SELECT 
                YEAR(transaction_date) AS year,
                SUM(amount) AS total_installment 
            FROM customer_account_invoices
            WHERE YEAR(transaction_date) IN (%s, %s) AND description = 'Instalment'
            GROUP BY YEAR(transaction_date)
            """
            installment_df = pd.read_sql(total_installment_query, user_db_conn, params=(current_year, previous_year))
            
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
                installment_df = pd.read_sql(total_installment_query, user_db_conn, params=(current_year, previous_year))
                
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
        
        #Top Project for selected year
        try:
            top_project_query = """
            SELECT project_id, SUM(sale_value) AS total_value 
            FROM Stands 
            WHERE YEAR(registration_date) = %s
            GROUP BY project_id 
            ORDER BY total_value DESC 
            LIMIT 1
            """
            top_project_df = pd.read_sql(top_project_query, user_db_conn, params=(current_year,))
            top_project_name = str(top_project_df.iloc[0]['project_id']) if not top_project_df.empty else "None"
            top_project_amount = top_project_df.iloc[0]['total_value'] if not top_project_df.empty else 0
        except Exception as e:
            top_project_name = "None"
            top_project_amount = 0
        
        formatted_top_project_amount = f"${top_project_amount:,.2f}" if top_project_amount else "$0"
        
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
        
        #Deposits vs Installments for selected year
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
        
        #Stands Sold Over the Years (last 5 years)
        try:
            start_year = current_year - 4  
            number_of_stands_query = """
            SELECT 
                YEAR(registration_date) AS year,
                COUNT(stand_number) AS total_stands_sold 
            FROM Stands 
            WHERE YEAR(registration_date) >= %s
            GROUP BY YEAR(registration_date)
            ORDER BY year
            """
            number_of_stands_df = pd.read_sql(number_of_stands_query, user_db_conn, params=(start_year,))
            
            if not number_of_stands_df.empty:
                all_years = list(range(start_year, current_year + 1))
                existing_years = number_of_stands_df['year'].tolist()                
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
            else:
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
            area_fig = go.Figure()
            area_fig.update_layout(
                title='Total Stands Sold Over the Years',
                xaxis_title='Year',
                yaxis_title='Number of Stands Sold',
                template='plotly_white',
                height=400
            )

        return [status, formatted_stand_value, formatted_stands_sold, formatted_deposit, 
                formatted_installment, top_project_name, period_text, period_text,
                period_text, period_text, formatted_top_project_amount, str(current_year),
                pie_fig, area_fig,
                stand_value_yoy, stands_sold_yoy, deposit_yoy, installment_yoy]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        period_text = f"Year: {selected_year}" if selected_year else "Year: --"
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        default_yoy = html.Span([
            html.I(className="fas fa-minus-circle me-1 text-muted"),
            "N/A"
        ], className="text-muted small")
        
        return [error_alert, "$0", "0", "$0", "$0", "None", 
                period_text, period_text, period_text, period_text, "$0", "--" if not selected_year else str(selected_year),
                empty_fig, empty_fig,
                default_yoy, default_yoy, default_yoy, default_yoy]
    
def calculate_percentage_change(current, previous):
    if previous == 0:
        if current == 0:
            return "+0% from previous year"
        else:
            return f"+∞% from previous year"
    else:
        change = ((current - previous) / previous) * 100
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.1f}% from previous year"

# Function to get user-specific database connection
def get_user_db_connection():
    if 'db_config' in session and session['db_config']:
        try:
            config = session['db_config']
            connection = mysql.connector.connect(**config)
            return connection
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

# Function to get connection status component for navbar
def get_connection_status_component():
    if 'db_config' in session and session['db_config']:
        try:
            config = session['db_config']
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE() as db_name")
            result = cursor.fetchone()
            db_name = result[0] if result else "Unknown"
            cursor.close()
            connection.close()
            
            return html.Div([
                html.Span([
                    html.I(className="fas fa-check-circle text-success me-1"),
                    f"Connected: {db_name}"
                ], className="text-success small")
            ], className="d-flex align-items-center")
        except:
            return html.Div([
                html.Span([
                    html.I(className="fas fa-exclamation-triangle text-warning me-1"),
                    "Connection Lost"
                ], className="text-warning small")
            ], className="d-flex align-items-center")
    else:
        return html.Div([
            html.Span([
                html.I(className="fas fa-times-circle text-danger me-1"),
                "Not Connected"
            ], className="text-danger small")
        ], className="d-flex align-items-center")

if __name__ == '__main__':
    app.run(debug=True)