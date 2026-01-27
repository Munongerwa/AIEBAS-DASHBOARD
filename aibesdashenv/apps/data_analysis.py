import dash_bootstrap_components as dbc
from dash import html, dcc
from flask import session
from sqlalchemy import create_engine

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
        html.I(className="fas fa-chart-bar me-2"),
        "Data Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="analysis-connection-status"),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-analytics me-2"),
                        "Select Analysis Type"
                    ], className="bg-primary text-white"),
                    dbc.CardBody([
                        html.P("Choose the type of analysis you want to perform:", className="mb-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-map-marked-alt fa-2x text-success mb-3"),
                                            html.H5("Land Bank Analysis", className="card-title"),
                                            html.P("Analyze land inventory and availability", className="card-text"),
                                            dbc.Button([
                                                html.I(className="fas fa-arrow-right me-2"),
                                                "Go to Analysis"
                                            ], 
                                            href="/apps/land_bank_analysis", 
                                            color="success", 
                                            className="mt-2")
                                        ], className="text-center")
                                    ])
                                ], className="h-100")
                            ], width=12, md=4, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-project-diagram fa-2x text-primary mb-3"),
                                            html.H5("Project Analysis", className="card-title"),
                                            html.P("Analyze project performance and metrics", className="card-text"),
                                            dbc.Button([
                                                html.I(className="fas fa-arrow-right me-2"),
                                                "Go to Analysis"
                                            ], 
                                            href="/apps/project_analysis", 
                                            color="primary", 
                                            className="mt-2")
                                        ], className="text-center")
                                    ])
                                ], className="h-100")
                            ], width=12, md=4, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.I(className="fas fa-money-bill-wave fa-2x text-info mb-3"),
                                            html.H5("Sales Analysis", className="card-title"),
                                            html.P("Analyze sales performance and trends", className="card-text"),
                                            dbc.Button([
                                                html.I(className="fas fa-arrow-right me-2"),
                                                "Go to Analysis"
                                            ], 
                                            href="/apps/sales_analysis", 
                                            color="info", 
                                            className="mt-2")
                                        ], className="text-center")
                                    ])
                                ], className="h-100")
                            ], width=12, md=4, className="mb-3")
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="mt-4")
])