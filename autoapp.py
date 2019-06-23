"""Create an application instance."""
from app.app import create_app
import atexit
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler


app = create_app()
app.app_context().push()



