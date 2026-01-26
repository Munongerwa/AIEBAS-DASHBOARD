import dash
from dash import html
from apps import dashboard, db_connection

# Create Home Layout
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
    },
    children=[
        html.H1("Welcome to Aibes Analysis", style={'fontSize': '5rem', 'margin': '0'}),
        html.P("Your one-stop solution for Aibes Data Insights.", style={'fontSize': '1.5rem', 'margin': '15px 0'}),
        html.Div(
            [
                html.A("Get Started", href="/apps/db_connection", className='btn btn-primary', style={'marginTop': '20px', 'padding': '10px 20px'}),
            ]
        )
    ]
)