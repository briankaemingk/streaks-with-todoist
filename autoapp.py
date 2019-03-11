"""Create an application instance."""
from app.app import create_app
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

def print_date_time():
    print('Timer run')

scheduler = BackgroundScheduler()
scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


app = create_app()
app.app_context().push()

