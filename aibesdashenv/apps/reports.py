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
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reprts")
        self.ensure_reports_directory()
        
    def ensure_reports_directory(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def get_weekly_data(self, year, week_number):
        """Fetch data for the specified week"""
        if not self.db_connection_string:
            return {}
            
        try:
            engine = create_engine(self.db_connection_string)
            
            # Calculate date range for the week
            # Find Monday of the specified week
            jan_1 = datetime(year, 1, 1)
            days_to_monday = (7 - jan_1.weekday()) % 7
            week_start = jan_1 + timedelta(days=days_to_monday + (week_number - 2) * 7)
            week_end = week_start + timedelta(days=6)
            
            date_condition = f"DATE(registration_date) BETWEEN '{week_start.strftime('%Y-%m-%d')}' AND '{week_end.strftime('%Y-%m-%d')}'"
            transaction_date_condition = f"DATE(transaction_date) BETWEEN '{week_start.strftime('%Y-%m-%d')}' AND '{week_end.strftime('%Y-%m-%d')}'"
            
            # Total Stand Value
            total_stand_value_query = f"""
            SELECT SUM(sale_value) AS total_sale_value
            FROM Stands
            WHERE {date_condition}
            """
            stand_value_df = pd.read_sql(total_stand_value_query, engine)
            total_stand_value = stand_value_df.iloc[0]['total_sale_value'] if not stand_value_df.empty and not pd.isna(stand_value_df.iloc[0]['total_sale_value']) else 0
            
            #Number of Stands Sold
            stands_sold_query = f"""
            SELECT COUNT(stand_number) AS total_stands_sold
            FROM Stands
            WHERE {date_condition}
            """
            stands_sold_df = pd.read_sql(stands_sold_query, engine)
            total_stands_sold = stands_sold_df.iloc[0]['total_stands_sold'] if not stands_sold_df.empty and not pd.isna(stands_sold_df.iloc[0]['total_stands_sold']) else 0
            
            #Total Deposit
            total_deposit_query = f"""
            SELECT SUM(deposit_amount) AS total_deposit
            FROM customer_accounts
            WHERE {date_condition}
            """
            deposit_df = pd.read_sql(total_deposit_query, engine)
            total_deposit = deposit_df.iloc[0]['total_deposit'] if not deposit_df.empty and not pd.isna(deposit_df.iloc[0]['total_deposit']) else 0
            
            #Total Installment
            total_installment_query = f"""
            SELECT SUM(amount) AS total_installment
            FROM customer_account_invoices
            WHERE {transaction_date_condition} AND description = 'Instalment'
            """
            installment_df = pd.read_sql(total_installment_query, engine)
            total_installment = installment_df.iloc[0]['total_installment'] if not installment_df.empty and not pd.isna(installment_df.iloc[0]['total_installment']) else 0
            
            engine.dispose()
            
            return {
                'total_stand_value': total_stand_value,
                'total_stands_sold': total_stands_sold,
                'total_deposit': total_deposit,
                'total_installment': total_installment,
                'week_start': week_start,
                'week_end': week_end,
                'week_number': week_number,
                'year': year
            }
        except Exception as e:
            print(f"Error fetching weekly data: {e}")
            return {}
    
    def create_weekly_trend_chart(self, year, week_number):
        """Create a trend chart for the past 4 weeks"""
        try:
            if not self.db_connection_string:
                return None
                
            engine = create_engine(self.db_connection_string)
            
            # last 4 weeks
            weeks_data = []
            for i in range(4, 0, -1):
                target_week = week_number - i + 1
                if target_week < 1:
                    target_year = year - 1
                    # Approximate week calculation for previous year
                    target_week = 52 + target_week
                else:
                    target_year = year
                    
                week_data = self.get_weekly_data(target_year, target_week)
                if week_data:
                    weeks_data.append({
                        'week': f"Wk {target_week}",
                        'stands_sold': week_data['total_stands_sold']
                    })
            
            if not weeks_data:
                return None
            
            #matplotlib chart
            fig, ax = plt.subplots(figsize=(8, 4))
            weeks = [d['week'] for d in weeks_data]
            values = [d['stands_sold'] for d in weeks_data]
            
            ax.plot(weeks, values, marker='o', linewidth=2, markersize=6, color='#007bff')
            ax.set_title('Stands Sold - Last 4 Weeks', fontsize=14, pad=20)
            ax.set_xlabel('Week', fontsize=12)
            ax.set_ylabel('Stands Sold', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Improvement of styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Saving to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            print(f"Error creating trend chart: {e}")
            return None
    
    def generate_pdf_report(self, year, week_number):
        """Generate PDF report for the specified week"""
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
                alignment=1,  # Center align
                textColor=colors.HexColor("#007bff")
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor("#6c757d")
            )
            
            story.append(Paragraph("Weekly Sales Report", title_style))
            story.append(Spacer(1, 20))
            
            # Report metadata
            meta_style = styles['Normal']
            story.append(Paragraph(f"<b>Week:</b> {week_number}", meta_style))
            story.append(Paragraph(f"<b>Period:</b> {data['week_start'].strftime('%Y-%m-%d')} to {data['week_end'].strftime('%Y-%m-%d')}", meta_style))
            story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
            story.append(Spacer(1, 30))
            
            # Summary table
            data_table = [
                ['Metric', 'Value'],
                ['Total Stand Value', f"${data['total_stand_value']:,.2f}"],
                ['Stands Sold', str(data['total_stands_sold'])],
                ['Total Deposit', f"${data['total_deposit']:,.2f}"],
                ['Total Installment', f"${data['total_installment']:,.2f}"]
            ]
            
            table = Table(data_table, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
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
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Trend chart
            chart_img = self.create_weekly_trend_chart(year, week_number)
            if chart_img:
                story.append(Paragraph("Trend Analysis - Last 4 Weeks", subtitle_style))
                story.append(Spacer(1, 12))
                
                # Add chart image
                img_buffer = io.BytesIO(chart_img.getvalue())
                story.append(Image(img_buffer, width=6*inch, height=3*inch))
            
            # Build PDF
            doc.build(story)
            
            # Store report info in database
            self.store_report_info(filename, year, week_number, data)
            
            return filepath
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    def store_report_info(self, filename, year, week_number, data):
        """Store report information in SQLite database"""
        try:
            db_path = os.path.join(self.reports_dir, "reports.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    year INTEGER,
                    week_number INTEGER,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_stand_value REAL,
                    total_stands_sold REAL,
                    total_deposit REAL,
                    total_installment REAL
                )
            ''')
            
            # Insert report info
            cursor.execute('''
                INSERT OR REPLACE INTO reports 
                (filename, year, week_number, total_stand_value, total_stands_sold, total_deposit, total_installment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, year, week_number,
                data['total_stand_value'], data['total_stands_sold'],
                data['total_deposit'], data['total_installment']
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
                SELECT filename, year, week_number, generated_date, total_stand_value, total_stands_sold
                FROM reports
                ORDER BY generated_date DESC
                LIMIT 50
            ''')
            
            reports = cursor.fetchall()
            conn.close()
            
            return [{
                'filename': r[0], 
                'year': r[1], 
                'week': r[2], 
                'date': r[3],
                'total_stand_value': r[4],
                'total_stands_sold': r[5]
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