import dash
from dash import html
from apps import dashboard, db_connection


layout = html.Div(
    style={
        'backgroundImage': 'url(/assets/backimage.png)',
        'backgroundSize': 'cover',
        'height': '100vh',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'color': 'white',
        'textAlign': 'center',
        'marginTop': '0px'
    },
    children=[
        html.Img(src='/assets/aibes.png', style={'width': '210px', 'marginBottom': '20px',  'marginTop': '0px'}),
        html.H1("Welcome to Aibes Analysis", style={'fontSize': '4rem', 'marginTop': '0px'}),
        html.P("Your one-stop solution for Aibes Data Insights.", style={'fontSize': '1.8rem', 'margin': '15px 0'}),
        
        html.Div(
            style={
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '5px',
                'marginTop': '40px'
            },
            children=[
                html.A(
                    [html.I(className="fas fa-database me-2"), "Connect to Database"], 
                    href="/apps/db_connection", 
                    className='btn btn-primary btn-lg',
                    style={'padding': '10px 25px', 'fontSize': '1.2rem', 'marginTop': '10px'}
                ),       
            ]
        ),
        #Footer text
        html.P(
            "© 2026 Aibes Analysis. All rights reserved.", 
            style={
                'position': 'fixed',
                'marginTop': '30px',
                'bottom': '1px',
                'fontSize': '0.9rem',
                'textAlign': 'right',
                'opacity': '0.8'
            }
        )
    ]
)