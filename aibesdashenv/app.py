# app.py
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
from flask import session
from sqlalchemy import create_engine
import datetime
import uuid
import sqlite3
import os
from apps import home, dashboard, db_connection, data_analysis, land_bank_analysis, project_analysis, sales_analysis, reports_view, settings
from flask import session, send_from_directory
from apps.settings import layout, get_settings_manager, initialize_settings_manager
from flask import send_from_directory

# Initialize the Dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
                ],
                suppress_callback_exceptions=True,
                server=True)

#server-side session support
app.server.secret_key = 'bati-aibes'  

# Serve generated reports 
@app.server.route('/generated_reports/<path:filename>')
def serve_report(filename):
    reports_dir = os.path.join(os.path.dirname(__file__), "generated_reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return send_from_directory(reports_dir, filename)

@app.server.route('/serve-logo/<path:filename>')
def serve_logo(filename):
    logos_dir = os.path.join(os.path.dirname(__file__), "logos")
    if not os.path.exists(logos_dir):
        os.makedirs(logos_dir)
    return send_from_directory(logos_dir, filename)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    #multi-user session management
    dcc.Store(id='session-id'),  # For multi-user session management
    
    # navbar (top)
    dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/aibes.png", style={"height": "3rem", 'margin-right': '20px'}),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink([html.I(className="fas fa-home me-2"), "Home"], href="/", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-grip me-2"), "Dashboard"], href="/apps/dashboard", active="exact"),
                        dbc.DropdownMenu([
                            dbc.DropdownMenuItem("Land Bank", href="/apps/land_bank_analysis"),
                            dbc.DropdownMenuItem("Project Analysis", href="/apps/project_analysis"),
                            dbc.DropdownMenuItem("Sales Analysis", href="/apps/sales_analysis"),
                        ], nav=True, in_navbar=True, label="Analysis Modules", toggle_class_name="dropdown-toggle"),
                        dbc.NavLink([html.I(className="fas fa-file-pdf me-2"), "Reports"], href="/apps/reports_view", active="exact"),
                        dbc.NavLink([html.I(className="fas fa-database me-2"), "Database"], href="/apps/db_connection", active="exact", id="db-nav-link"),
                        dbc.NavLink([html.I(className="fas fa-cogs me-2"), "Settings"], href="/apps/settings", active="exact"),

                    ],
                    className="me-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
            # Connection Status in Navbar
            html.Div(id="navbar-connection-status", className="d-flex align-items-center ms-2"),
        ]),
        color="dark",
        dark=True,
        className="mb-20"
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
    #connection status for navbar
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
    
    #protected pages 
    protected_pages = [
        '/apps/dashboard', 
        '/apps/settings', 
        '/apps/land_bank_analysis', 
        '/apps/project_analysis', 
        '/apps/sales_analysis', 
        '/apps/reports_view'
    ]
    
    if pathname in protected_pages:
        if not get_user_db_connection():
            #protected pages error
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
    
    # Check if already connected
    if pathname == '/apps/db_connection':
        if get_user_db_connection():
            #already connected message
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
        
    #page routing
    if pathname == '/':
        return [home.layout, connection_status]
    elif pathname == '/apps/db_connection':
        return [db_connection.layout, connection_status]
    elif pathname == '/apps/dashboard':
        return [dashboard.layout, connection_status]
    elif pathname == '/apps/land_bank_analysis':
        return [land_bank_analysis.layout, connection_status]
    elif pathname == '/apps/project_analysis':
        return [project_analysis.layout, connection_status]
    elif pathname == '/apps/sales_analysis':
        return [sales_analysis.layout, connection_status]
    elif pathname == '/apps/reports_view':
        return [reports_view.layout, connection_status]
    elif pathname == '/apps/settings':
        return [settings.layout, connection_status]


    else:
        not_found = dbc.Container([
            html.H1("404 - Page not found"),
            html.P("The requested page does not exist."),
            dbc.Button("Go Home", href="/", color="primary", className="mt-3")
        ], className="text-center mt-5")
        return [not_found, connection_status]

settings_manager = initialize_settings_manager()
# Callback for navbar toggle
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    prevent_initial_call=False
)
def toggle_navbar_collapse(n):
    if n:
        return not False  
    return False
# Add this to your app.py startup
def initialize_email_settings():
    """Initialize email settings in database"""
    try:
        settings_db_path = os.path.join(os.path.dirname(__file__), "settings.db")
        conn = sqlite3.connect(settings_db_path)
        cursor = conn.cursor()
        
        # Create email settings table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY,
                smtp_server TEXT,
                smtp_port INTEGER,
                email_username TEXT,
                email_password TEXT,
                sender_email TEXT,
                sender_name TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default email settings if none exist
        cursor.execute("SELECT COUNT(*) FROM email_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO email_settings (id, smtp_server, smtp_port) 
                VALUES (1, 'smtp.gmail.com', 587)
            ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing email settings: {e}")

# Call this function during app initialization
initialize_email_settings()
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
def initialize_database_tables():
    """Initialize all required database tables"""
    try:
        settings_db_path = os.path.join(os.path.dirname(__file__), "settings.db")
        conn = sqlite3.connect(settings_db_path)
        cursor = conn.cursor()
        
        # Create company settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY,
                company_name TEXT,
                logo_path TEXT,
                logo_data BLOB,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create email settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY,
                smtp_server TEXT,
                smtp_port INTEGER,
                email_username TEXT,
                email_password TEXT,
                sender_email TEXT,
                sender_name TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default company settings if none exist
        cursor.execute("SELECT COUNT(*) FROM company_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO company_settings (id, company_name) 
                VALUES (1, 'AIBES Real Estate')
            ''')
        
        # Insert default email settings if none exist
        cursor.execute("SELECT COUNT(*) FROM email_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO email_settings (id, smtp_server, smtp_port) 
                VALUES (1, 'smtp.gmail.com', 587)
            ''')
        
        conn.commit()
        conn.close()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
# Function to get connection status component for navbar
def get_connection_status_component():
    if 'db_connection_string' in session and session['db_connection_string']:
        try:
            engine = create_engine(session['db_connection_string'])
            connection = engine.connect()
            # Get database name 
            db_name = session['db_connection_string'].split('/')[-1]
            connection.close()
            
            return html.Div([
                html.Span([
                    html.I(className="fas fa-check-circle text-success me-1"),
                    f"Connected: {db_name}"
                ], className="text-success small")
            ], className="d-flex align-items-center")
        except Exception as e:
            print(f"Connection status check error: {e}")
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
    initialize_database_tables()
    app.run(debug=True)