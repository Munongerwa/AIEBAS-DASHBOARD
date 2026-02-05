# scheduler_setup.py
from apscheduler.schedulers.background import BackgroundScheduler
from apps.reports import get_report_generator
import datetime
import atexit

def generate_weekly_report_job():
    """Job to generate weekly reports every Monday"""
    try:
        current_date = datetime.datetime.now()
        current_year = current_date.year
        current_week = current_date.isocalendar()[1]
        
        # Generate report for previous week
        previous_week = current_week - 1
        previous_year = current_year
        if previous_week < 1:
            previous_year -= 1
            previous_week = 52  
            
        generator = get_report_generator()
        if generator:
            filepath = generator.generate_pdf_report(previous_year, previous_week)
            if filepath:
                print(f"[AUTO] Weekly report generated: {filepath}")
            else:
                print("[AUTO] Failed to generate weekly report")
    except Exception as e:
        print(f"[AUTO] Error generating weekly report: {e}")

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    # Run every Monday at 2 AM
    scheduler.add_job(
        func=generate_weekly_report_job,
        trigger="cron",
        day_of_week="mon",
        hour=2,
        minute=0
    )
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler