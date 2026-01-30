# apps/reports_view.py
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, no_update, State, ctx, ALL
from flask import session
import os
import json
from .reports import get_report_generator
import datetime
import dash
from dateutil.relativedelta import relativedelta

# Layout - Make sure this is defined at the module level
layout = html.Div([
    dbc.Container([
        # Report Generation Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-file-pdf me-2"),
                        "Generate New Report"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Report Type", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="report-type-dropdown",
                                        options=[
                                            {"label": "Daily", "value": "daily"},
                                            {"label": "Weekly", "value": "weekly"},
                                            {"label": "Monthly", "value": "monthly"},
                                            {"label": "Yearly", "value": "yearly"},
                                            {"label": "Custom Range", "value": "custom"}
                                        ],
                                        value="weekly",
                                        className="mb-3"
                                    ),
                                ], width=12, md=4),
                                
                                dbc.Col([
                                    dbc.Label("Start Date", className="fw-bold"),
                                    dcc.DatePickerSingle(
                                        id="report-start-date",
                                        date=datetime.date.today() - datetime.timedelta(days=7),
                                        className="mb-3 w-100"
                                    ),
                                ], width=12, md=4),
                                
                                dbc.Col([
                                    dbc.Label("End Date", className="fw-bold"),
                                    dcc.DatePickerSingle(
                                        id="report-end-date",
                                        date=datetime.date.today(),
                                        className="mb-3 w-100"
                                    ),
                                ], width=12, md=4),
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-file-pdf me-2"),
                                        "Generate Report"
                                    ], id="generate-custom-report-btn", color="success", size="lg", className="w-100 mb-2"),
                                ], width=12, md=4),
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-sync me-2"),
                                        "Refresh Reports"
                                    ], id="refresh-reports-btn", color="primary", size="lg", className="w-100 mb-2"),
                                ], width=12, md=4),
                            ], className="mt-3"),
                        ])
                    ])
                ], className="shadow-sm mb-4"),
            ], width=12)
        ]),
        
        # Status messages
        html.Div(id="generate-report-status", className="mb-3"),
        
        # Email Sharing Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-paper-plane me-2"),
                "Email Report"
            ])),
            dbc.ModalBody([
                html.Div(id="email-modal-report-info", className="mb-3"),
                dbc.Form([
                    dbc.Label("Recipient Email(s)", className="fw-bold"),
                    dbc.Input(
                        id="email-recipient-input",
                        type="text",
                        placeholder="recipient@example.com, another@example.com",
                        className="mb-3"
                    ),
                    dbc.Label("Subject", className="fw-bold"),
                    dbc.Input(
                        id="email-subject-input",
                        type="text",
                        placeholder="Sales Report",
                        className="mb-3"
                    ),
                    dbc.Label("Message", className="fw-bold"),
                    dbc.Textarea(
                        id="email-message-input",
                        placeholder="Please find the attached sales report.",
                        className="mb-3",
                        style={"height": "100px"}
                    ),
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-paper-plane me-2"),
                    "Send Email"
                ], id="send-email-btn", color="success"),
                dbc.Button("Cancel", id="cancel-email-btn", color="secondary"),
            ])
        ], id="email-modal", size="lg"),
        
        # Reports List Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-history me-2"),
                        "Generated Reports"
                    ], className="fw-bold"),
                    dbc.CardBody([
                        html.Div(id="reports-table-container"),
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
    """Generate the reports table"""
    if not reports:
        return dbc.Alert("No reports found.", color="info")
    
    # Create table header
    table_header = [
        html.Thead([
            html.Tr([
                html.Th("Report Name", style={"width": "25%"}),
                html.Th("Type", style={"width": "12%"}),
                html.Th("Period", style={"width": "23%"}),
                html.Th("Generated Date", style={"width": "15%"}),
                html.Th("Actions", style={"width": "25%"})
            ])
        ])
    ]
    
    # Create table rows
    rows = []
    for report in reports:
        try:
            # Parse dates
            start_date = datetime.datetime.strptime(report['start_date'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(report['end_date'], '%Y-%m-%d').date()
            generated_date = datetime.datetime.strptime(report['date'], '%Y-%m-%d %H:%M:%S')
            
            row = html.Tr([
                html.Td(html.Strong(report['filename'])),
                html.Td(report['report_type'].title(), className="text-center"),
                html.Td(f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"),
                html.Td(generated_date.strftime('%Y-%m-%d'), className="text-center"),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-download me-1"),
                        ], 
                        href=f"/generated_reports/{report['filename']}",
                        size="sm",
                        color="success",
                        title="Download"),
                        dbc.Button([
                            html.I(className="fas fa-paper-plane me-1"),
                        ], 
                        id={"type": "email-report", "index": report['filename']},
                        size="sm",
                        color="info",
                        title="Email"),
                        dbc.Button([
                            html.I(className="fas fa-share-alt me-1"),
                        ], 
                        id={"type": "share-report", "index": report['filename']},
                        size="sm",
                        color="warning",
                        title="Share"),
                        dbc.Button([
                            html.I(className="fas fa-eye me-1"),
                        ], 
                        id={"type": "preview-report", "index": report['filename']},
                        size="sm",
                        color="primary",
                        title="Preview")
                    ], size="sm")
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

# Callback to update date pickers based on report type
@callback(
    [Output("report-start-date", "date"),
     Output("report-end-date", "date")],
    Input("report-type-dropdown", "value"),
    prevent_initial_call=False
)
def update_date_range(report_type):
    end_date = datetime.date.today()
    
    if report_type == "daily":
        start_date = end_date
    elif report_type == "weekly":
        start_date = end_date - datetime.timedelta(days=7)
    elif report_type == "monthly":
        start_date = end_date - relativedelta(months=1)
    elif report_type == "yearly":
        start_date = end_date - relativedelta(years=1)
    else:  # custom
        start_date = end_date - datetime.timedelta(days=7)
    
    return start_date, end_date

@callback(
    Output("generate-report-status", "children"),
    Input("generate-custom-report-btn", "n_clicks"),
    [State("report-type-dropdown", "value"),
     State("report-start-date", "date"),
     State("report-end-date", "date")],
    prevent_initial_call=True
)
def generate_custom_report(n_clicks, report_type, start_date_str, end_date_str):
    """Generate a report for custom date range"""
    if n_clicks is None:
        return no_update
    
    try:
        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Validate date range
        if start_date > end_date:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Start date cannot be after end date."
            ], color="danger")
        
        # Limit date range to prevent excessive data processing
        if (end_date - start_date).days > 365:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Maximum date range is 365 days."
            ], color="warning")
        
        generator = get_report_generator()
        if not generator and session.get('db_connection_string'):
            from .reports import initialize_report_generator
            generator = initialize_report_generator(session['db_connection_string'])
        
        if generator:
            # Generate report
            filepath = generator.generate_pdf_report(start_date, end_date, report_type)
            
            if filepath:
                filename = os.path.basename(filepath)
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Report generated successfully: {filename}"
                ], color="success")
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Failed to generate report. Please check the logs."
                ], color="warning")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Reports system not initialized. Please connect to database first."
            ], color="danger")
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error generating report: {str(e)}"
        ], color="danger")

# Email Modal Callbacks
@callback(
    [Output("email-modal", "is_open"),
     Output("email-modal-report-info", "children"),
     Output("email-recipient-input", "value"),
     Output("email-subject-input", "value"),
     Output("email-message-input", "value")],
    Input({"type": "email-report", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def open_email_modal(n_clicks):
    if not ctx.triggered:
        return False, no_update, "", "", ""
    
    try:
        # Extract filename from triggered_id
        triggered_id = ctx.triggered[0]['prop_id']
        if '.n_clicks' in triggered_id:
            # Handle pattern matching callback
            prop_id = triggered_id.replace('.n_clicks', '')
            if prop_id.startswith('{'):
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
            else:
                filename = prop_id
        else:
            return False, no_update, "", "", ""
        
        if filename:
            # Default email content
            subject = f"Sales Report: {filename}"
            message = f"Please find the attached sales report: {filename}"
            
            info_content = html.Div([
                html.H6([
                    html.I(className="fas fa-file-pdf me-2"),
                    f"Email Report: {filename}"
                ]),
                html.Small("Enter recipient email(s) and customize the message below", className="text-muted")
            ])
            
            return True, info_content, "", subject, message
        else:
            return False, "", "", "", ""
    except Exception as e:
        return False, dbc.Alert(f"Error: {str(e)}", color="danger"), "", "", ""

@callback(
    Output("email-modal", "is_open", allow_duplicate=True),
    [Input("cancel-email-btn", "n_clicks"),
     Input("send-email-btn", "n_clicks")],
    prevent_initial_call=True
)
def close_email_modal(n1, n2):
    return False

@callback(
    Output("generate-report-status", "children", allow_duplicate=True),
    Input("send-email-btn", "n_clicks"),
    [State("email-recipient-input", "value"),
     State("email-subject-input", "value"),
     State("email-message-input", "value"),
     State("email-modal-report-info", "children")],
    prevent_initial_call=True
)
def send_email_report(n_clicks, recipients, subject, message, report_info):
    if n_clicks is None:
        return no_update
    
    try:
        # Extract filename from report info
        filename = None
        if report_info and hasattr(report_info, 'children') and len(report_info.children) > 1:
            # Try to extract filename from the H6 element
            if hasattr(report_info.children[0], 'children'):
                text_content = report_info.children[0].children
                if isinstance(text_content, str) and ": " in text_content:
                    filename = text_content.split(": ")[1]
        
        if not filename:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Could not determine report file"
            ], color="danger")
        
        # Validate inputs
        if not recipients:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Please enter at least one recipient email"
            ], color="danger")
        
        # Parse recipients
        recipient_list = [email.strip() for email in recipients.split(',')]
        
        generator = get_report_generator()
        if not generator:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Reports system not initialized"
            ], color="danger")
        
        # Get full file path
        filepath = os.path.join(generator.reports_dir, filename)
        if not os.path.exists(filepath):
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Report file not found: {filename}"
            ], color="danger")
        
        # Send email
        success, result_message = generator.send_report_via_email(
            filepath, recipient_list, subject, message
        )
        
        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Email sent successfully to {len(recipient_list)} recipient(s)!"
            ], color="success")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Failed to send email: {result_message}"
            ], color="danger")
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error sending email: {str(e)}"
        ], color="danger")

# Preview callback
@callback(
    [Output("report-preview-modal", "is_open"),
     Output("report-preview-content", "children")],
    [Input({"type": "preview-report", "index": ALL}, "n_clicks"),
     Input("close-preview", "n_clicks")],
    prevent_initial_call=True
)
def toggle_preview_modal(preview_clicks, close_clicks):
    from dash import callback_context
    
    if not callback_context.triggered:
        return False, no_update
    
    triggered_id = callback_context.triggered[0]['prop_id']
    
    # Handle close button
    if 'close-preview' in triggered_id:
        return False, no_update
    
    # Handle preview button - extract filename from triggered_id
    try:
        # Extract filename from triggered_id
        if '.n_clicks' in triggered_id:
            prop_id = triggered_id.replace('.n_clicks', '')
            if prop_id.startswith('{'):
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
            else:
                filename = prop_id
        else:
            filename = "unknown"
        
        if filename and filename != "unknown":
            # Check if file exists
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
            file_path = os.path.join(reports_dir, filename)
            
            if os.path.exists(file_path):
                # Create preview content with iframe for PDF viewing
                preview_content = html.Div([
                    html.H5([
                        html.I(className="fas fa-file-pdf me-2"),
                        f"Report: {filename}"
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.A([
                                dbc.Button([
                                    html.I(className="fas fa-external-link-alt me-2"),
                                    "Open PDF in New Tab"
                                ], color="primary", className="me-2")
                            ], href=f"/generated_reports/{filename}", target="_blank"),
                        ], width="auto"),
                        dbc.Col([
                            html.A([
                                dbc.Button([
                                    html.I(className="fas fa-download me-2"),
                                    "Download PDF"
                                ], color="success")
                            ], href=f"/generated_reports/{filename}"),
                        ], width="auto")
                    ], className="mb-3"),
                    
                    html.Hr(),
                    html.P([
                        html.Strong("Report Preview:"),
                        html.Br(),
                        "PDF preview requires browser plugin. Use the buttons above for full report access."
                    ], className="small text-muted")
                ])
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
    except Exception as e:
        return True, dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error loading preview: {str(e)}"
        ], color="danger")

# Share callback
@callback(
    [Output("report-preview-modal", "is_open", allow_duplicate=True),
     Output("report-preview-content", "children", allow_duplicate=True)],
    Input({"type": "share-report", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def share_report(share_clicks):
    from dash import callback_context
    
    if not callback_context.triggered:
        return False, no_update
    
    try:
        # Extract filename from triggered_id
        triggered_id = callback_context.triggered[0]['prop_id']
        if '.n_clicks' in triggered_id:
            prop_id = triggered_id.replace('.n_clicks', '')
            if prop_id.startswith('{'):
                triggered_dict = json.loads(prop_id)
                filename = triggered_dict.get('index')
            else:
                filename = prop_id
        else:
            filename = "unknown"
        
        if filename and filename != "unknown":
            # Generate shareable link and QR code
            base_url = "http://yourdomain.com"  # Replace with your actual domain
            shareable_link = f"{base_url}/generated_reports/{filename}"
            
            # In a real app, you'd generate a QR code here
            # For now, we'll just show the link
            share_content = html.Div([
                html.H5([
                    html.I(className="fas fa-share-alt me-2"),
                    f"Share Report: {filename}"
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Shareable Link", className="card-title"),
                        html.Div([
                            dbc.Input(
                                value=shareable_link,
                                readOnly=True,
                                className="mb-2"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-copy me-2"),
                                "Copy Link"
                            ], id="copy-link-btn", color="primary", size="sm")
                        ])
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardBody([
                        html.H6("QR Code", className="card-title"),
                        html.P("QR code would appear here in a real implementation", className="text-muted"),
                        # In real implementation: html.Img(src="/api/qrcode?url={shareable_link}")
                    ])
                ], className="mb-3"),
                
                html.Small("Note: Anyone with this link can access the report.", className="text-muted")
            ])
            
            return True, share_content
        else:
            return True, dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Invalid report selection."
            ], color="danger")
    except Exception as e:
        return True, dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error preparing share: {str(e)}"
        ], color="danger")