"""Create an application instance."""
from app.app import create_app, hourly
import atexit
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler


app = create_app()
app.app_context().push()


scheduler = BackgroundScheduler()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown(wait=False))
scheduler.add_job(func=hourly, args=app, trigger="cron", minute=33, timezone=utc)
scheduler.start()
