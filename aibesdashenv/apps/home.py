import dash
from dash import html
import dash_bootstrap_components as dbc

# Define CSS styles separately
welcome_styles = """
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(0px); }
    }
    
    .welcome-container:hover .feature-card {
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    .cta-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.5) !important;
        text-decoration: none !important;
    }
    
    body {
        margin: 0;
        overflow-x: hidden;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
"""

layout = html.Div([
    # Include CSS styles
    html.Div(welcome_styles, style={'display': 'none'}),
    
    html.Div(
        style={
            'background': 'linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url(/assets/backimage.png)',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center',
            'height': '100vh',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
            'color': 'white',
            'textAlign': 'center',
            'padding': '15px'
        },
        children=[
            # Main content container - REDUCED SIZE
            html.Div(
                style={
                    'width': '100%',
                    'maxWidth': '600px',
                    'padding': '30px 25px',
                    'backgroundColor': 'rgba(15, 23, 42, 0.85)',
                    'borderRadius': '15px',
                    'boxShadow': '0 15px 35px rgba(0, 0, 0, 0.5)',
                    'backdropFilter': 'blur(8px)',
                    'border': '1px solid rgba(255, 255, 255, 0.1)',
                    'position': 'relative',
                    'overflow': 'hidden',
                    'className': 'welcome-container',
                    'minHeight': '450px'
                },
                children=[
                    # Decorative elements - Reduced size
                    html.Div(style={
                        'position': 'absolute',
                        'top': '-30px',
                        'right': '-30px',
                        'width': '100px',
                        'height': '100px',
                        'border': '2px solid rgba(56, 189, 248, 0.2)',
                        'borderRadius': '50%',
                    }),
                    html.Div(style={
                        'position': 'absolute',
                        'bottom': '-20px',
                        'left': '-20px',
                        'width': '70px',
                        'height': '70px',
                        'border': '2px solid rgba(16, 185, 129, 0.2)',
                        'borderRadius': '50%',
                    }),
                    
                    # Logo and heading - Reduced sizes
                    html.Div(
                        style={
                            'marginBottom': '20px',
                            'position': 'relative',
                            'zIndex': '2'
                        },
                        children=[
                            html.Img(
                                src='/assets/aibes.png', 
                                style={
                                    'width': '140px',
                                    'marginBottom': '15px',
                                    'filter': 'drop-shadow(0 3px 10px rgba(0, 0, 0, 0.3))',
                                    'animation': 'float 3s ease-in-out infinite'
                                }
                            ),
                            html.H1(
                                "Aibes Analytics", 
                                style={
                                    'fontSize': '2.2rem',
                                    'fontWeight': '700',
                                    'margin': '0 0 10px 0',
                                    'background': 'linear-gradient(90deg, #38bdf8, #10b981)',
                                    'WebkitBackgroundClip': 'text',
                                    'WebkitTextFillColor': 'transparent',
                                    'letterSpacing': '0.5px'
                                }
                            ),
                        ]
                    ),
                    
                    # Description - Reduced font size
                    html.P(
                        "Transform your data into powerful insights",
                        style={
                            'fontSize': '1.1rem',
                            'margin': '0 0 25px 0',
                            'lineHeight': '1.5',
                            'opacity': '0.9',
                            'maxWidth': '450px',
                            'marginLeft': 'auto',
                            'marginRight': 'auto',
                            'position': 'relative',
                            'zIndex': '2'
                        }
                    ),
                    
                    # Feature cards - Reduced sizes and spacing
                    html.Div(
                        style={
                            'display': 'flex',
                            'justifyContent': 'center',
                            'gap': '15px',
                            'marginBottom': '25px',
                            'flexWrap': 'wrap',
                            'position': 'relative',
                            'zIndex': '2'
                        },
                        children=[
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-bolt", style={'fontSize': '1.4rem', 'marginBottom': '8px', 'color': '#38bdf8'}),
                                    html.H4("Real-time", style={'margin': '0 0 5px 0', 'fontSize': '0.9rem', 'fontWeight': '600'}),
                                    html.P("Instant insights", style={'fontSize': '0.8rem', 'opacity': '0.7', 'margin': '0'})
                                ], style={'textAlign': 'center'})
                            ], style={
                                'backgroundColor': 'rgba(30, 41, 59, 0.6)',
                                'padding': '15px',
                                'borderRadius': '10px',
                                'width': '110px',
                                'border': '1px solid rgba(56, 189, 248, 0.1)',
                                'className': 'feature-card',
                                'transition': 'all 0.3s ease'
                            }),
                            
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-brain", style={'fontSize': '1.4rem', 'marginBottom': '8px', 'color': '#10b981'}),
                                    html.H4("AI-Powered", style={'margin': '0 0 5px 0', 'fontSize': '0.9rem', 'fontWeight': '600'}),
                                    html.P("Smart analysis", style={'fontSize': '0.8rem', 'opacity': '0.7', 'margin': '0'})
                                ], style={'textAlign': 'center'})
                            ], style={
                                'backgroundColor': 'rgba(30, 41, 59, 0.6)',
                                'padding': '15px',
                                'borderRadius': '10px',
                                'width': '110px',
                                'border': '1px solid rgba(16, 185, 129, 0.1)',
                                'className': 'feature-card',
                                'transition': 'all 0.3s ease'
                            }),
                            
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-shield-alt", style={'fontSize': '1.4rem', 'marginBottom': '8px', 'color': '#8b5cf6'}),
                                    html.H4("Secure", style={'margin': '0 0 5px 0', 'fontSize': '0.9rem', 'fontWeight': '600'}),
                                    html.P("Data protection", style={'fontSize': '0.8rem', 'opacity': '0.7', 'margin': '0'})
                                ], style={'textAlign': 'center'})
                            ], style={
                                'backgroundColor': 'rgba(30, 41, 59, 0.6)',
                                'padding': '15px',
                                'borderRadius': '10px',
                                'width': '110px',
                                'border': '1px solid rgba(139, 92, 246, 0.1)',
                                'className': 'feature-card',
                                'transition': 'all 0.3s ease'
                            })
                        ]
                    ),
                    
                    # DATABASE CONNECTION BUTTON 
                    html.A(
                        [html.I(className="fas fa-database me-1"), "Connect to Database"],
                        href="/apps/db_connection", 
                        className="cta-button",
                        style={
                            'padding': '12px 30px',
                            'fontSize': '1rem',
                            'borderRadius': '10px',
                            'fontWeight': '600',
                            'letterSpacing': '0.5px',
                            'boxShadow': '0 6px 20px rgba(16, 185, 129, 0.3)',
                            'transition': 'all 0.3s ease',
                            'border': 'none',
                            'background': 'linear-gradient(90deg, #10b981, #059669)',
                            'color': 'white',
                            'textDecoration': 'none',
                            'display': 'inline-block',
                            'position': 'relative',
                            'zIndex': '2',
                            'marginBottom': '20px',
                            'cursor': 'pointer'
                        }
                    ),
                    
                    # Additional Info Text - Reduced size
                    html.P(
                        "Get started by connecting to your data",
                        style={
                            'fontSize': '0.9rem',
                            'margin': '0 0 20px 0',
                            'opacity': '0.8',
                            'letterSpacing': '0.5px',
                            'position': 'relative',
                            'zIndex': '2'
                        }
                    ),
                    
                    # Footer text - Reduced size
                    html.P(
                        "© 2026 Aibes Analytics",
                        style={
                            'fontSize': '0.8rem',
                            'marginTop': '10px',
                            'opacity': '0.6',
                            'letterSpacing': '0.5px',
                            'position': 'relative',
                            'zIndex': '2'
                        }
                    )
                ]
            )
        ]
    )
])