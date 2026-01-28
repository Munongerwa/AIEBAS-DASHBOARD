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

class ReportGenerator:
    def __init__(self, db_connection_string=None):
        self.db_connection_string = db_connection_string
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
        self.ensure_reports_directory()
        
    def ensure_reports_directory(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def get_weekly_data(self, year, week_number):
        """Fetch data for the specified week grouped by project_id"""
        if not self.db_connection_string:
            return {}
            
        try:
            engine = create_engine(self.db_connection_string)
            
            # Calculation of the date range for the week
            jan_1 = datetime(year, 1, 1)
            days_to_monday = (7 - jan_1.weekday()) % 7
            week_start = jan_1 + timedelta(days=days_to_monday + (week_number - 2) * 7)
            week_end = week_start + timedelta(days=6)
            
            date_condition = f"DATE(registration_date) BETWEEN '{week_start.strftime('%Y-%m-%d')}' AND '{week_end.strftime('%Y-%m-%d')}'"
            transaction_date_condition = f"DATE(transaction_date) BETWEEN '{week_start.strftime('%Y-%m-%d')}' AND '{week_end.strftime('%Y-%m-%d')}'"
            
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
                'week_start': week_start,
                'week_end': week_end,
                'week_number': week_number,
                'year': year
            }
        except Exception as e:
            print(f"Error fetching weekly data: {e}")
            return {}
    
    def create_daily_trend_chart(self, year, week_number):
        """Create a trend chart showing daily sales for the week"""
        try:
            if not self.db_connection_string:
                return None
                
            engine = create_engine(self.db_connection_string)
            
            # Calculate date range for the week
            jan_1 = datetime(year, 1, 1)
            days_to_monday = (7 - jan_1.weekday()) % 7
            week_start = jan_1 + timedelta(days=days_to_monday + (week_number - 2) * 7)
            week_end = week_start + timedelta(days=6)
            
            date_condition = f"DATE(registration_date) BETWEEN '{week_start.strftime('%Y-%m-%d')}' AND '{week_end.strftime('%Y-%m-%d')}'"
            
            # Get daily data for the week
            daily_query = f"""
            SELECT 
                DATE(registration_date) as sale_date,
                COUNT(stand_number) AS stands_sold
            FROM Stands
            WHERE {date_condition}
            GROUP BY DATE(registration_date)
            ORDER BY sale_date
            """
            daily_df = pd.read_sql(daily_query, engine)
            
            engine.dispose()
            
            if daily_df.empty:
                return None
            
            # Create daily trend chart
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Convert dates to readable format
            daily_df['sale_date'] = pd.to_datetime(daily_df['sale_date'])
            daily_df['date_label'] = daily_df['sale_date'].dt.strftime('%a\n%m/%d')
            
            ax.bar(daily_df['date_label'], daily_df['stands_sold'], 
                   color='#007bff', alpha=0.7, edgecolor='#0056b3')
            
            ax.set_title('Daily Stands Sold - This Week', fontsize=14, pad=20)
            ax.set_xlabel('Day of Week', fontsize=12)
            ax.set_ylabel('Stands Sold', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for i, v in enumerate(daily_df['stands_sold']):
                ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')
            
            # Improve styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylim(0, daily_df['stands_sold'].max() * 1.2)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating daily trend chart: {e}")
            return None
    
    def generate_pdf_report(self, year, week_number):
        """Generate PDF report for the specified week with project grouping"""
        try:
            # weekly data
            data = self.get_weekly_data(year, week_number)
            if not data:
                return None
            
            # filename
            filename = f"weekly_report_{year}_W{week_number:02d}.pdf"
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
            
            story.append(Paragraph("AIBES Weekly Sales Report", title_style))
            story.append(Spacer(1, 20))
            
            # Report metadata
            meta_style = styles['Normal']
            story.append(Paragraph(f"<b>Week:</b> {week_number}", meta_style))
            story.append(Paragraph(f"<b>Period:</b> {data['week_start'].strftime('%Y-%m-%d')} to {data['week_end'].strftime('%Y-%m-%d')}", meta_style))
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
            
            story.append(Paragraph("Weekly Summary", subtitle_style))
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
            chart_img = self.create_daily_trend_chart(year, week_number)
            if chart_img:
                story.append(Paragraph("Daily Trend Analysis - This Week", subtitle_style))
                story.append(Spacer(1, 12))
                
                # chart image
                img_buffer = io.BytesIO(chart_img.getvalue())
                story.append(Image(img_buffer, width=7*inch, height=3.5*inch))
            
            # code for building the PDF
            doc.build(story)
            
            # report info in database storing
            self.store_report_info(filename, year, week_number, summary_data)
            
            return filepath
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    def store_report_info(self, filename, year, week_number, summary_data):
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
                    year INTEGER,
                    week_number INTEGER,
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
                (filename, year, week_number, total_stand_value, total_stands_sold, total_stands_available, total_deposit, total_installment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, year, week_number,
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
                SELECT filename, year, week_number, generated_date, total_stand_value, total_stands_sold, total_stands_available
                FROM reports
                ORDER BY generated_date DESC
                LIMIT 60
            ''')
            
            reports = cursor.fetchall()
            conn.close()
            
            return [{
                'filename': r[0], 
                'year': r[1], 
                'week': r[2], 
                'date': r[3],
                'total_stand_value': r[4],
                'total_stands_sold': r[5],
                'total_stands_available': r[6]
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