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
        html.I(className="fas fa-map-marked-alt me-2"),
        "Land Bank Analysis"
    ], className="mt-3 mb-4 text-center"),
    
    # Connection status indicator
    html.Div(id="land-bank-connection-status"),
    
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
                                    id="land-bank-year-dropdown",
                                    options=[
                                        {'label': str(year), 'value': year} 
                                        for year in range(datetime.datetime.now().year, datetime.datetime.now().year - 5, -1)
                                    ],
                                    value=datetime.datetime.now().year,
                                    clearable=False,
                                    className="mb-2"
                                )
                            ], width=6),
                            
                            dbc.Col([
                                dbc.Label("Select Project", className="mb-2"),
                                dcc.Dropdown(
                                    id="land-bank-project-dropdown",
                                    options=[],
                                    placeholder="Select a project",
                                    className="mb-2"
                                )
                            ], width=4),

                            
                            
                        ]),
                        
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Analysis"
                        ], id="refresh-land-bank-button", color="primary", className="w-50")
                    ])
                ])
            ], width=12)
        ], className="mb-3"),
        
        # Metric Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Total Stands Sold", className="card-title text-center"),
                            html.H2(id="total-stands", children="0 stands", className="text-center text-success fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Available Stands", className="card-title text-center"),
                            html.H2(id="available-stands", children="0 stands", className="text-center text-primary fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Commercial Stands", className="card-title text-center"),
                            html.H2(id="commercial-stands", children="0 stands", className="text-center text-warning fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4, className="mb-2"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Residential Stands", className="card-title text-center"),
                            html.H2(id="residential-stands", children="0 stands", className="text-center text- fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4),
            
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H4("Sold Stands", className="card-title text-center"),
                            html.H2(id="sold-stands", children="0 stands", className="text-center text-info fw-bold"),
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=4)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-pie me-2"),
                        "Land Distribution by Status"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="land-status-pie-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Land Area by Project"
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="land-project-bar-chart", style={"height": "400px"})
                    ])
                ], className="mb-4")
            ], width=12, md=6)
        ])
    ], className="mt-4", fluid=True)
])

# Callback to load project options
@callback(
    Output("land-bank-project-dropdown", "options"),
    Input("land-bank-year-dropdown", "value")
)
def load_project_options(selected_year):
    engine = get_user_db_engine()
    if not engine:
        return []
    
    try:
        query = "SELECT DISTINCT project_id FROM Stands ORDER BY project_id"
        df = pd.read_sql(query, engine)
        options = [{'label': f"Project {row['project_id']}", 'value': row['project_id']} for _, row in df.iterrows()]

        return options
    
    

    except Exception as e:
        return []
    finally:
        if engine:
            engine.dispose()

#callback for land bank analysis
@callback(
    [Output("land-bank-connection-status", "children"),
     Output("total-stands", "children"),
     Output("available-stands", "children"),
     Output("sold-stands", "children"),
     Output("commercial-stands", "children"),
     Output("residential-stands", "children"),
     Output("land-status-pie-chart", "figure"),
     Output("land-project-bar-chart", "figure")],
    [Input("refresh-land-bank-button", "n_clicks")],
    [Input("land-bank-year-dropdown", "value"),
     Input("land-bank-project-dropdown", "value")]
)
def update_land_bank_analysis(n_clicks, selected_year, selected_project):
    engine = get_user_db_engine()
    
    if not engine:
        not_connected_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Not connected to database. Please connect first."
        ], color="warning")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No Data - Please Connect to Database")
        
        return [not_connected_alert, "0 sq ft", "0 sq ft", "0%", empty_fig, empty_fig]
    
    try:
        # Build query based on filters
        where_clause = f"WHERE YEAR(registration_date) = {selected_year}"
        if selected_project:
            where_clause += f" AND project_id = {selected_project}"
        
        # TOTAL STANDS
        total_stands_query = f"""
        SELECT COUNT(stand_number) AS total_stands FROM Stands {where_clause}
        """
        total_df = pd.read_sql(total_stands_query, engine)
        total_stands = total_df.iloc[0]['total_stands'] if not total_df.empty and total_df.iloc[0]['total_stands'] else 0
        formatted_total_stands = f"{total_stands:,.0f} stands" if total_stands else "0 stands"
        
        # Available Land stands
        available_stands_query = f"""
        SELECT COUNT(stand_number) AS available_stands FROM Stands {where_clause} AND available = 1
        """
        available_df = pd.read_sql(available_stands_query, engine)
        available_stands = available_df.iloc[0]['available_stands'] if not available_df.empty and available_df.iloc[0]['available_stands'] else 0
        formatted_available_stands = f"{available_stands:,.0f} stands" if available_stands else "0 stands"
        
        #STANDS sold

        sold_stands_query = f"""
        SELECT COUNT(stand_number) AS sold_stands FROM Stands {where_clause} AND available = 0
        """
        sold_df = pd.read_sql(sold_stands_query, engine)
        sold_stands = sold_df.iloc[0]['sold_stands'] if not sold_df.empty and sold_df.iloc[0]['sold_stands'] else 0
        formatted_sold_stands = f"{sold_stands:,.0f} stands" if sold_stands else "0 stands"

        #commercial stands sold
        commercial_stands_query = f"""
        SELECT COUNT(stand_number) AS commercial_stands FROM Stands {where_clause} AND available = 0 AND property_description_id = 2
        """
        commercial_df = pd.read_sql(commercial_stands_query, engine)
        commercial_stands = commercial_df.iloc[0]['commercial_stands'] if not commercial_df.empty and commercial_df.iloc[0]['commercial_stands'] else 0
        formatted_commercial_stands = f"{commercial_stands:,.0f} stands" if commercial_stands else "0 stands"

        #residential stands sold
        residential_stands_query = f"""
        SELECT COUNT(stand_number) AS residential_stands FROM Stands {where_clause} AND available = 0 AND property_description_id = 1
        """
        residential_df = pd.read_sql(residential_stands_query, engine)
        residential_stands = residential_df.iloc[0]['residential_stands'] if not residential_df.empty and residential_df.iloc[0]['residential_stands'] else 0
        formatted_residential_stands = f"{residential_stands:,.0f} stands" if residential_stands else "0 stands"


        # Land Distribution by Status (Pie Chart)
        status_query = f"""
        SELECT available, COUNT(stand_number) AS area FROM Stands {where_clause} GROUP BY available
        """
        status_df = pd.read_sql(status_query, engine)
        
        if not status_df.empty:
            pie_fig = go.Figure(data=[go.Pie(
                labels=status_df['available'], 
                values=status_df['area'],
                hole=0.6
            )])
            pie_fig.update_layout(title="Land Distribution by Status")
        else:
            pie_fig = go.Figure()
            pie_fig.update_layout(title="No Data Available")
        
        # Land Area by Project (Bar Chart)
        project_query = f"""
        SELECT project_id, SUM(stand_number) AS total_area FROM Stands {where_clause} GROUP BY project_id ORDER BY total_area DESC
        """
        project_df = pd.read_sql(project_query, engine)
        
        if not project_df.empty:
            bar_fig = go.Figure(data=[go.Bar(
                x=[f"Project {row['project_id']}" for _, row in project_df.iterrows()],
                y=project_df['total_area'],
                marker_color='lightblue'
            )])
            bar_fig.update_layout(
                title="Land Area by Project",
                xaxis_title="Project",
                yaxis_title="Land Area (sq ft)"
            )
        else:
            bar_fig = go.Figure()
            bar_fig.update_layout(title="No Data Available")
        
        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Connected to database successfully! Showing data for Year: {selected_year}" + (f", Project: {selected_project}" if selected_project else "")
        ], color="success")
        
        return [status, formatted_total_stands , formatted_available_stands, formatted_sold_stands, formatted_commercial_stands, formatted_residential_stands, pie_fig, bar_fig]
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Database error: {str(e)}"
        ], color="danger")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error Loading Data")
        
        return [error_alert, "0 sq ft", "0 sq ft", "0%", empty_fig, empty_fig]
    finally:
        if engine:
            engine.dispose()