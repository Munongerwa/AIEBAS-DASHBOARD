# apps/reports.py
import os
import sqlite3
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  
import io
from sqlalchemy import create_engine
import pandas as pd
from reportlab.platypus import PageBreak
import qrcode
from urllib.parse import quote
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl

class ReportGenerator:
    def __init__(self, db_connection_string=None):
        self.db_connection_string = db_connection_string
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
        self.ensure_reports_directory()
        
    def ensure_reports_directory(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def get_company_info(self):
        """Get company information from settings"""
        try:
            settings_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.db")
            if os.path.exists(settings_db_path):
                conn = sqlite3.connect(settings_db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT company_name, logo_path FROM company_settings WHERE id = 1
                ''')
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    return {
                        'company_name': result[0] or 'AIBES Real Estate',
                        'logo_path': result[1]
                    }
            return {
                'company_name': 'AIBES Real Estate',
                'logo_path': None
            }
        except Exception as e:
            print(f"Error getting company info: {e}")
            return {
                'company_name': 'AIBES Real Estate',
                'logo_path': None
            }
    
    def get_email_settings(self):
        """Get email configuration from settings"""
        try:
            settings_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.db")
            if os.path.exists(settings_db_path):
                conn = sqlite3.connect(settings_db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT smtp_server, smtp_port, email_username, email_password, sender_email, sender_name
                    FROM email_settings WHERE id = 1
                ''')
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:  # Check if smtp_server exists
                    return {
                        'smtp_server': result[0] or 'smtp.gmail.com',
                        'smtp_port': result[1] or 587,
                        'username': result[2],
                        'password': result[3],
                        'sender_email': result[4],
                        'sender_name': result[5] or 'AIBES Reports System'
                    }
            return None
        except Exception as e:
            print(f"Error getting email settings: {e}")
            return None
    
    def get_custom_data(self, start_date, end_date, report_type="custom"):
        """Fetch data for custom date range"""
        if not self.db_connection_string:
            return {}
            
        try:
            engine = create_engine(self.db_connection_string)
            
            # Format dates for SQL
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            date_condition = f"DATE(registration_date) BETWEEN '{start_date_str}' AND '{end_date_str}'"
            transaction_date_condition = f"DATE(transaction_date) BETWEEN '{start_date_str}' AND '{end_date_str}'"
            
            # Get project-based data using project_id only
            project_data_query = f"""
            SELECT 
                project_id,
                COUNT(stand_number) AS stands_sold,
                SUM(sale_value) AS stands_value,
                COUNT(CASE WHEN available = 0 THEN stand_number END) AS stands_available
            FROM Stands
            WHERE {date_condition}
            GROUP BY project_id
            ORDER BY stands_sold DESC
            """
            project_df = pd.read_sql(project_data_query, engine)
            
            # Get overall summary
            summary_query = f"""
            SELECT 
                COUNT(stand_number) AS total_stands_sold,
                SUM(sale_value) AS total_stand_value,
                COUNT(CASE WHEN available = 0 THEN stand_number END) AS total_stands_available
            FROM Stands
            WHERE {date_condition}
            """
            summary_df = pd.read_sql(summary_query, engine)
            
            # Total Deposit
            total_deposit_query = f"""
            SELECT SUM(deposit_amount) AS total_deposit
            FROM customer_accounts
            WHERE {date_condition}
            """
            deposit_df = pd.read_sql(total_deposit_query, engine)
            total_deposit = deposit_df.iloc[0]['total_deposit'] if not deposit_df.empty and not pd.isna(deposit_df.iloc[0]['total_deposit']) else 0
            
            # Total Installment
            total_installment_query = f"""
            SELECT SUM(amount) AS total_installment
            FROM customer_account_invoices
            WHERE {transaction_date_condition} AND description = 'Instalment'
            """
            installment_df = pd.read_sql(total_installment_query, engine)
            total_installment = installment_df.iloc[0]['total_installment'] if not installment_df.empty and not pd.isna(installment_df.iloc[0]['total_installment']) else 0
            
            # Get daily trend data
            daily_trend_query = f"""
            SELECT 
                DATE(registration_date) as sale_date,
                COUNT(stand_number) AS stands_sold
            FROM Stands
            WHERE {date_condition}
            GROUP BY DATE(registration_date)
            ORDER BY sale_date
            """
            daily_trend_df = pd.read_sql(daily_trend_query, engine)
            
            engine.dispose()
            
            return {
                'project_data': project_df,
                'summary': {
                    'total_stand_value': summary_df.iloc[0]['total_stand_value'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stand_value']) else 0,
                    'total_stands_sold': summary_df.iloc[0]['total_stands_sold'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stands_sold']) else 0,
                    'total_stands_available': summary_df.iloc[0]['total_stands_available'] if not summary_df.empty and not pd.isna(summary_df.iloc[0]['total_stands_available']) else 0,
                    'total_deposit': total_deposit,
                    'total_installment': total_installment
                },
                'daily_trend': daily_trend_df,
                'start_date': start_date,
                'end_date': end_date,
                'report_type': report_type
            }
        except Exception as e:
            print(f"Error fetching custom data: {e}")
            return {}
    
    def create_daily_trend_chart(self, daily_trend_df, title="Daily Sales Trend"):
        """Create a trend chart showing daily sales"""
        try:
            if daily_trend_df.empty:
                return None
            
            # Create daily trend chart
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Convert dates to readable format
            daily_trend_df['sale_date'] = pd.to_datetime(daily_trend_df['sale_date'])
            daily_trend_df['date_label'] = daily_trend_df['sale_date'].dt.strftime('%m/%d')
            
            ax.bar(daily_trend_df['date_label'], daily_trend_df['stands_sold'], 
                   color='#007bff', alpha=0.7, edgecolor='#0056b3')
            
            ax.set_title(title, fontsize=14, pad=20)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Stands Sold', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for i, v in enumerate(daily_trend_df['stands_sold']):
                ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')
            
            # Improve styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylim(0, daily_trend_df['stands_sold'].max() * 1.2)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating daily trend chart: {e}")
            return None
    
    def generate_shareable_link(self, filename):
        """Generate a shareable link for the report"""
        try:
            encoded_filename = quote(filename)
            return f"http://yourdomain.com/generated_reports/{encoded_filename}"
        except Exception as e:
            print(f"Error generating shareable link: {e}")
            return None
    
    def generate_qr_code(self, url):
        """Generate QR code for sharing"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return img_buffer
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
    
    def send_report_via_email(self, filepath, recipient_emails, subject=None, message=None):
        """Send report via email"""
        try:
            # Get email settings
            email_settings = self.get_email_settings()
            if not email_settings:
                return False, "Email settings not configured. Please configure email settings in the Settings page."
            
            # Check required fields
            if not email_settings.get('username') or not email_settings.get('password'):
                return False, "Email username and password not configured."
            
            if not email_settings.get('sender_email'):
                return False, "Sender email address not configured."
            
            if not recipient_emails:
                return False, "No recipient emails provided"
            
            # Default values
            if not subject:
                subject = f"Sales Report - {os.path.basename(filepath)}"
            
            if not message:
                message = "<p>Please find the attached sales report.</p>"
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{email_settings['sender_name']} <{email_settings['sender_email']}>"
            msg['To'] = ", ".join(recipient_emails) if isinstance(recipient_emails, list) else recipient_emails
            msg['Subject'] = subject
            
            # Add HTML body
            html_body = f"""
            <html>
                <body>
                    <h2>Sales Report</h2>
                    <p>{message}</p>
                    <hr>
                    <p><em>This is an automated message from {email_settings['sender_name']}</em></p>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachment
            if os.path.exists(filepath):
                with open(filepath, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(filepath)}'
                )
                msg.attach(part)
            else:
                return False, f"Report file not found: {filepath}"
            
            # Send email
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(email_settings['username'], email_settings['password'])
                    server.send_message(msg)
                
                return True, "Report sent successfully"
            except smtplib.SMTPAuthenticationError:
                return False, "Email authentication failed. Please check your username and password."
            except smtplib.SMTPRecipientsRefused:
                return False, "All recipient addresses were refused. Please check the email addresses."
            except smtplib.SMTPServerDisconnected:
                return False, "SMTP server disconnected. Please check your SMTP settings."
            except Exception as e:
                return False, f"Failed to send email: {str(e)}"
                
        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"Failed to send email: {str(e)}"
    
    def generate_pdf_report(self, start_date, end_date, report_type="custom"):
        """Generate PDF report for custom date range with company branding"""
        try:
            # Get data
            data = self.get_custom_data(start_date, end_date, report_type)
            if not data:
                return None
            
            # Get company info
            company_info = self.get_company_info()
            
            # Generate filename
            filename = f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{report_type}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1, 
                textColor=colors.HexColor("#052191")
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor("#ac147e")
            )
            
            # Company Header
            if company_info['logo_path'] and os.path.exists(company_info['logo_path']):
                try:
                    logo_img = Image(company_info['logo_path'], width=2*inch, height=1*inch)
                    story.append(logo_img)
                    story.append(Spacer(1, 10))
                except:
                    pass  # Skip if logo can't be loaded
            
            story.append(Paragraph(company_info['company_name'], title_style))
            story.append(Paragraph("Sales Report", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Report metadata
            meta_style = styles['Normal']
            story.append(Paragraph(f"<b>Report Type:</b> {report_type.title()}", meta_style))
            story.append(Paragraph(f"<b>Period:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", meta_style))
            story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
            story.append(Spacer(1, 30))
            
            # Overall Summary table
            summary_data = data['summary']
            summary_table_data = [
                ['Metric', 'Value'],
                ['Total Stand Value', f"${summary_data['total_stand_value']:,.2f}"],
                ['Total Stands Sold', str(summary_data['total_stands_sold'])],
                ['Total Stands Available', str(summary_data['total_stands_available'])],
                ['Total Deposit', f"${summary_data['total_deposit']:,.2f}"],
                ['Total Installment', f"${summary_data['total_installment']:,.2f}"]
            ]
            
            summary_table = Table(summary_table_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#007bff")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            story.append(Paragraph("Summary", subtitle_style))
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Project-wise Analysis table
            if not data['project_data'].empty:
                story.append(Paragraph("Project-wise Analysis", subtitle_style))
                
                # Prepare project table data
                project_table_data = [['Project ID', 'Stands Sold', 'Value ($)', 'Stands Available']]
                
                for _, row in data['project_data'].iterrows():
                    project_table_data.append([
                        str(int(row['project_id'])) if pd.notna(row['project_id']) else 'N/A',
                        str(int(row['stands_sold'])) if pd.notna(row['stands_sold']) else '0',
                        f"${row['stands_value']:,.2f}" if pd.notna(row['stands_value']) else '$0.00',
                        str(int(row['stands_available'])) if pd.notna(row['stands_available']) else '0'
                    ])
                
                # Add totals row
                if len(data['project_data']) > 1:
                    total_stands_sold = data['project_data']['stands_sold'].sum()
                    total_value = data['project_data']['stands_value'].sum()
                    total_available = data['project_data']['stands_available'].sum()
                    
                    project_table_data.append([
                        'TOTAL', 
                        str(int(total_stands_sold)),
                        f"${total_value:,.2f}",
                        str(int(total_available))
                    ])
                
                project_table = Table(project_table_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 2*inch])
                
                # Define base table styles
                project_table_styles = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#28a745")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 10),
                ]

                # Conditionally add bold/colored footer only if multiple rows exist
                if len(data['project_data']) > 1:
                    project_table_styles.extend([
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e9ecef"))
                    ])

                project_table.setStyle(TableStyle(project_table_styles))
                
                story.append(project_table)
                story.append(Spacer(1, 30))
            
            # Daily trend chart
            chart_img = self.create_daily_trend_chart(data['daily_trend'], f"Daily Sales Trend ({report_type.title()})")
            if chart_img:
                story.append(Paragraph("Daily Trend Analysis", subtitle_style))
                story.append(Spacer(1, 12))
                
                # chart image
                img_buffer = io.BytesIO(chart_img.getvalue())
                story.append(Image(img_buffer, width=7*inch, height=3.5*inch))
                story.append(PageBreak())
            
            # Sharing section
            story.append(Paragraph("Share This Report", subtitle_style))
            
            # Generate shareable link
            shareable_link = self.generate_shareable_link(filename)
            if shareable_link:
                story.append(Paragraph(f"<b>Direct Link:</b> <link href='{shareable_link}'>{shareable_link}</link>", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Generate QR code
                qr_code_img = self.generate_qr_code(shareable_link)
                if qr_code_img:
                    story.append(Paragraph("Scan to Access Report:", styles['Normal']))
                    qr_buffer = io.BytesIO(qr_code_img.getvalue())
                    story.append(Image(qr_buffer, width=2*inch, height=2*inch))
            
            # Build PDF
            doc.build(story)
            
            # Store report info in database
            self.store_report_info(filename, start_date, end_date, report_type, summary_data)
            
            return filepath
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    def store_report_info(self, filename, start_date, end_date, report_type, summary_data):
        """Store report information in SQLite database"""
        try:
            db_path = os.path.join(self.reports_dir, "reports.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Creating table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    start_date DATE,
                    end_date DATE,
                    report_type TEXT,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_stand_value REAL,
                    total_stands_sold INTEGER,
                    total_stands_available INTEGER,
                    total_deposit REAL,
                    total_installment REAL
                )
            ''')
            
            # Inserting the report information
            cursor.execute('''
                INSERT OR REPLACE INTO reports 
                (filename, start_date, end_date, report_type, total_stand_value, total_stands_sold, total_stands_available, total_deposit, total_installment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), report_type,
                summary_data['total_stand_value'], summary_data['total_stands_sold'],
                summary_data['total_stands_available'], summary_data['total_deposit'], 
                summary_data['total_installment']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error storing report info: {e}")
    
    def get_generated_reports(self):
        """Get list of generated reports"""
        try:
            db_path = os.path.join(self.reports_dir, "reports.db")
            if not os.path.exists(db_path):
                return []
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, start_date, end_date, report_type, generated_date, 
                       total_stand_value, total_stands_sold, total_stands_available
                FROM reports
                ORDER BY generated_date DESC
                LIMIT 60
            ''')
            
            reports = cursor.fetchall()
            conn.close()
            
            return [{
                'filename': r[0], 
                'start_date': r[1],
                'end_date': r[2],
                'report_type': r[3],
                'date': r[4],
                'total_stand_value': r[5],
                'total_stands_sold': r[6],
                'total_stands_available': r[7]
            } for r in reports]
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

# Global report generator instance
report_generator = None

def initialize_report_generator(db_connection_string):
    """Initialize the global report generator"""
    global report_generator
    report_generator = ReportGenerator(db_connection_string)
    return report_generator

def get_report_generator():
    """Get the global report generator instance"""
    global report_generator
    return report_generator