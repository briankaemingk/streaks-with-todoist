# Streaks with Todoist 
Enhancements to native behavior in todoist to improve motivation, focus, and flow.

## Installation

Visit [SwT homepage](https://streaks-with-todoist.herokuapp.com) to enable this integration and read about the features that it enables.

## Installing a local copy

### Pre-requisites

1. Install [PostgreSQL locally](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)
2. Create a database role using `sudo -u postgres createuser -s [default_user_name]`
3. Install [virtualenv](https://virtualenv.pypa.io/en/latest/installation/) and [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
4. Create a new [Todoist account](http://todoist.com) for testing purposes 
5. Create a new app in the [Todoist app console](https://developer.todoist.com/appconsole.html):
    * Create a new app called Streaks with Todoist STAGING
    * Add an OAuth redirect URL: https://stage-streaks-with-todoist.serveo.net/oauth_callback
    * Click Save Settings
    * Scroll down to the Webhooks section: Select Webhooks version 7
    * Set Webhook callback URL to https://stage-streaks-with-todoist.serveo.net/webhook_callback
    * Check the fields for item:added, item:complete, item:updated, reminder:fired
    * Click Save webhook configurations


### Local Installation

1. Clone the repo: `git clone https://github.com/briankaemingk/streaks-with-todoist.git`
2. Create the virtualenv
    ```
    $ virtualenv .venv  
    $ source .venv/bin/activate
    ```
3. Install the requirement packages:  `$ pip3 install -r requirements.txt`
4. Initiate the database:
    ```
    $ python manage.py db init
    $ python manage.py db migrate
    $ python manage.py db upgrade 
    ```
5. Create an empty file called `.env` and add the following to it:
    ```
    DATABASE_URL=postgresql:///postgres
    APP_SETTINGS=config.DevelopmentConfig
    ```
    * Log into the [Todoist app console](https://developer.todoist.com/appconsole.html) to add the client id and client secret:
    ```
    CLIENT_ID=...jfdk34s...
    CLIENT_SECRET=...343j...
    ```    
6. Start a tunnel using serveo: `ssh -R stage-streaks-with-todoist:80:localhost:5000 serveo.net` 
7. Run the app locally using `flask run`

### Staging Installation

1. Create a heroku app for your staging app: `$ heroku create staging-appname`
2. Copy the client id and client secret from your .env file and set them as variables in your staging app:
    ```
    $ heroku config:set CLIENT_ID=...jfdk34s...
    $ heroku config:set CLIENT_SECRET=...343j...
    ```
3. In addition, set the APP_SETTINGS variable: `heroku config:set APP_SETTINGS=config.StagingConfig`
4. Push the app: `git push heroku master`
5. Log into the  Log into the [Todoist app console](https://developer.todoist.com/appconsole.html):
    * Change the OAuth redirect URL to your heroku app url: https://heroku_app_name.herokuapp.com/oauth_callback
    * Click Save Settings
    * Scroll down to the Webhooks section and set the Webhook callback URL to your heroku app url: https://heroku_app_name.herokuapp.com/webhook_callback
    * Click Save webhook configurations
    
### Database updates
If you make any updates to the database, you need to upgrade the database in your local and staging environments like this:

* Local: `$ python manage.py db upgrade`  
* Staging: `$ heroku run python manage.py db upgrade`
    * Running a command: `heroku pg:psql -c "command"`
* Re-creating the database:

```
>>> from app import db
>>> db.create_all()
>>> db.session.commit()
```

You can access the database locally with the following command: `$ sudo -u postgres psql
`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
