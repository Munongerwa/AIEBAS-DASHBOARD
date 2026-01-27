import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
from apps import home, dashboard, db_connection, data_analysis, land_bank_analysis, project_analysis, sales_analysis
from flask import session
from sqlalchemy import create_engine
import datetime
import uuid

# Initialize the Dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True)

# Add server-side session support
app.server.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Add custom CSS for purple color
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-id'),  # For multi-user session management
    
   

    # Top navigation bar with connection status
    dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/aibes.png", style={"width": "5.9rem", 'margin-right': '200px', 'margin-left': '0px'}),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink([html.I(className="fas fa-home me-2"), "Home"], href="/", active="exact"),
                        dbc.NavLink([html.I(className="fas fa- me-2"), "Dashboard"], href="/apps/dashboard", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-chart-bar me-2"), "Data Analysis"], href="/apps/data_analysis", active="exact"),
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
            # Connection Status in Navbar
            html.Div(id="navbar-connection-status", className="d-flex align-items-center ms-3"),
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    ),

    # Page content
    html.Div(id='page-content', children=[]),
])

# Session initialization callback
@app.callback(Output('session-id', 'data'),
              Input('url', 'pathname'))
def initialize_session(pathname):
    # Initialize session for each user
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['db_connection_string'] = None
    return session['user_id']

@app.callback([Output('page-content', 'children'),
               Output('navbar-connection-status', 'children')],
              [Input('url', 'pathname')])
def display_page(pathname):
    # Check connection status for navbar
    connection_status = get_connection_status_component()
    
    # Handle logout
    if pathname == '/apps/logout':
        # Clear user session
        session.pop('db_connection_string', None)
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
        ]), connection_status]
    
    # Check if trying to access dashboard without connection
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
            return [error_page, connection_status]
    
    # Check if trying to access data analysis pages without connection
    if pathname in ['/apps/data_analysis', '/apps/land_bank_analysis', '/apps/project_analysis', '/apps/sales_analysis']:
        if not get_user_db_connection():
            # Show error on analysis pages
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
            return [error_page, connection_status]
    
    # Check if trying to access login when already connected
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
                                html.I(className="fas fa-chart-line me-2"),
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
            return [already_connected_page, connection_status]
    
    # Normal page routing
    if pathname == '/':
        return [home.layout, connection_status]
    elif pathname == '/apps/db_connection':
        return [db_connection.layout, connection_status]
    elif pathname == '/apps/dashboard':
        return [dashboard.layout, connection_status]
    elif pathname == '/apps/data_analysis':
        return [data_analysis.layout, connection_status]
    elif pathname == '/apps/land_bank_analysis':
        return [land_bank_analysis.layout, connection_status]
    elif pathname == '/apps/project_analysis':
        return [project_analysis.layout, connection_status]
    elif pathname == '/apps/sales_analysis':
        return [sales_analysis.layout, connection_status]
    elif pathname == '/apps/about':
        return [html.Div([html.H1("About Page")]), connection_status]
    # Add additional pages as necessary
    else:
        not_found = dbc.Container([
            html.H1("404 - Page not found"),
            html.P("The requested page does not exist.")
        ])
        return [not_found, connection_status]

# Callback for navbar toggle
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    prevent_initial_call=False
)
def toggle_navbar_collapse(n):
    if n:
        return True
    return False

# Function to get user-specific database connection
def get_user_db_connection():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            return engine
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

# Function to get connection status component for navbar
def get_connection_status_component():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            connection = engine.connect()
            # Get database name from connection string
            db_name = session['db_connection_string'].split('/')[-1]
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