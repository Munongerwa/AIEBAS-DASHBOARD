# apps/reports_view.py
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, no_update
from flask import session
import os
import json
from .reports import get_report_generator
import datetime
import dash
# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-file-pdf me-2"),
                        "Generated Reports"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-sync me-2"),
                                    "Refresh Reports"
                                ], id="refresh-reports-btn", color="primary", className="mb-3")
                            ], width=12)
                        ]),
                        html.Div(id="reports-table-container")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        # Preview modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Report Preview"), close_button=True),
            dbc.ModalBody([
                html.Div(id="report-preview-content", children=[
                    html.P("Select a report to preview", className="text-muted text-center")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-preview", className="ms-auto", n_clicks=0)
            ])
        ], id="report-preview-modal", size="xl", backdrop="static")
    ], className="mt-4", fluid=True)
], className="bg-light min-vh-100 py-4")

def generate_reports_table(reports):
    """Generate the reports table without stands sold column"""
    if not reports:
        return dbc.Alert("No reports found.", color="info")
    
    # Create table header
    table_header = [
        html.Thead([
            html.Tr([
                html.Th("Report Name", style={"width": "40%"}),
                html.Th("Period", style={"width": "30%"}),
                html.Th("Generated Date", style={"width": "20%"}),
                html.Th("Actions", style={"width": "10%"})
            ])
        ])
    ]
    
    # Create table rows
    rows = []
    for report in reports:
        try:
            # Parse the date properly
            if isinstance(report['date'], str):
                generated_date = datetime.datetime.strptime(report['date'], '%Y-%m-%d %H:%M:%S')
            else:
                generated_date = report['date']
            
            # Calculate week start/end dates (approximate)
            week_start_date = generated_date - datetime.timedelta(days=generated_date.weekday())
            week_end_date = week_start_date + datetime.timedelta(days=6)
            
            row = html.Tr([
                html.Td(html.Strong(report['filename'])),
                html.Td(f"Week {report['week']} ({week_start_date.strftime('%Y-%m-%d')} to {week_end_date.strftime('%Y-%m-%d')})"),
                html.Td(generated_date.strftime('%Y-%m-%d %H:%M')),
                html.Td([
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Download"
                    ], 
                    href=f"/generated_reports/{report['filename']}",
                    size="sm",
                    color="success",
                    className="me-1"),
                    dbc.Button([
                        html.I(className="fas fa-eye me-1"),
                        "View"
                    ], 
                    id={"type": "preview-report", "index": report['filename']},
                    size="sm",
                    color="primary")
                ])
            ])
            rows.append(row)
        except Exception as e:
            print(f"Error processing report {report.get('filename', 'unknown')}: {e}")
            continue
    
    if not rows:
        return dbc.Alert("No valid reports found.", color="warning")
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)
    
    return table

@callback(
    Output("reports-table-container", "children"),
    Input("refresh-reports-btn", "n_clicks"),
    prevent_initial_call=False
)
def refresh_reports(n_clicks):
    """Refresh and display reports"""
    try:
        generator = get_report_generator()
        if not generator and session.get('db_connection_string'):
            from .reports import initialize_report_generator
            generator = initialize_report_generator(session['db_connection_string'])
        
        if generator:
            reports = generator.get_generated_reports()
            return generate_reports_table(reports)
        else:
            return dbc.Alert("Reports system not initialized. Please connect to database first.", color="warning")
    except Exception as e:
        return dbc.Alert(f"Error loading reports: {str(e)}", color="danger")

# Simplified callback for preview modal
@callback(
    Output("report-preview-modal", "is_open"),
    Output("report-preview-content", "children"),
    Input({"type": "preview-report", "index": dash.dependencies.ALL}, "n_clicks"),
    Input("close-preview", "n_clicks"),
    prevent_initial_call=True
)
def toggle_preview_modal(n1, n2):
    """Toggle report preview modal"""
    from dash import callback_context
    
    if not callback_context.triggered:
        return False, no_update
    
    triggered_prop_id = callback_context.triggered[0]['prop_id']
    
    # Handle close button
    if 'close-preview' in triggered_prop_id:
        return False, no_update
    
    # Handle preview button clicks
    try:
        # Extract filename from the triggered prop_id
        # Format: '{"type":"preview-report","index":"filename.pdf"}.n_clicks'
        if '.n_clicks' in triggered_prop_id:
            prop_id = triggered_prop_id.replace('.n_clicks', '')
            if prop_id.startswith('{'):
                # Parse JSON
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
            else:
                # Handle other formats
                filename = prop_id
        else:
            filename = "unknown"
        
        if filename and filename != "unknown":
            # Check if file exists
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
            file_path = os.path.join(reports_dir, filename)
            
            if os.path.exists(file_path):
                # Create preview content with iframe for PDF viewing
                preview_content = [
                    html.H5(f"Report: {filename}", className="mb-3"),
                    html.P("Click 'Open in New Tab' to view the full report:", className="text-muted"),
                    html.Div([
                        html.A([
                            dbc.Button([
                                html.I(className="fas fa-external-link-alt me-2"),
                                "Open PDF in New Tab"
                            ], color="primary", className="me-2")
                        ], href=f"/generated_reports/{filename}", target="_blank"),
                        html.A([
                            dbc.Button([
                                html.I(className="fas fa-download me-2"),
                                "Download PDF"
                            ], color="success")
                        ], href=f"/generated_reports/{filename}")
                    ], className="mb-3"),
                    html.Hr(),
                    html.P("Note: If the PDF doesn't display above, please use the 'Open in New Tab' button.", className="small text-muted")
                ]
                return True, preview_content
            else:
                return True, dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Report file '{filename}' not found on server."
                ], color="danger")
        else:
            return True, dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Invalid report selection."
            ], color="danger")
    except json.JSONDecodeError:
        # Handle case where prop_id is not valid JSON
        return True, dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Error processing report selection."
        ], color="danger")
    except Exception as e:
        return True, dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error loading preview: {str(e)}"
        ], color="danger")