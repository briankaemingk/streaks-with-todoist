"""Create an application instance."""
from app.app import create_app
from apscheduler.schedulers.blocking import BlockingScheduler

app = create_app()
app.app_context().push()

sched = BlockingScheduler()

@sched.scheduled_job('cron', minute=49)
def scheduled_job():
    print("Timer called")


sched.start()
