import dash_bootstrap_components as dbc
from dash import html, dcc
import datetime

# Dashboard layout
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
                        ], id="refresh-dashboard-button", color="primary", className="w-100")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        # Metrics Cards 
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
                                html.I(className="fas fa-store fa-2x text-primary"),
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
            ], width=12, md=6, lg=3)
        ], className="mb-4"),
        
        dbc.Row([
            # Top Project Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-project-diagram fa-2x text-danger"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Top Project", className="card-title text-center"),
                            html.H2(id="top-project-value", children="None", className="text-center text-danger fw-bold"),
                            html.P(id="top-project-amount", children="$0", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=4),
            
            # Year Info Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-calendar fa-2x text-purple"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Selected Year", className="card-title text-center"),
                            html.H2(id="selected-year-info", children="--", className="text-center text-purple fw-bold")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=6, lg=4),
            
            # Empty card to maintain grid
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-info-circle fa-2x text-secondary"),
                            ], className="d-flex justify-content-center mb-3"),
                            html.H4("Year-over-Year Comparison", className="card-title text-center"),
                            html.P("↑ ↓ icons show increase/decrease from previous year", className="text-center text-muted small")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=12, md=12, lg=4)
        ], className="mb-4"),
        
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