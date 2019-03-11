"""Create an application instance."""
from app.app import create_app

app = create_app()
app.app_context().push()

