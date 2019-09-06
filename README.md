# Streaks with Todoist 
Enhancements to native behavior in todoist to improve motivation, focus, and flow.

## Installation

Visit [SwT homepage](https://streaks-with-todoist.herokuapp.com) to enable this integration and read about the features that it enables.

## Installing a local copy

### Pre-requisites

1. Install PostgreSQL locally
```
sudo apt update
sudo apt install postgresql postgresql-contrib
```
2. Create a database using `sudo -u postgres createdb swt`
3. Install [virtualenv](https://virtualenv.pypa.io/en/latest/installation/) and [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
4. Create a new [Todoist account](http://todoist.com) for testing purposes 
5. Create a new app in the [Todoist app console](https://developer.todoist.com/appconsole.html):
    * Create a new app called Streaks with Todoist LOCAL
    * Add an OAuth redirect URL: https://local-streaks-with-todoist.serveo.net/oauth_callback
    * Click Save Settings
    * Scroll down to the Webhooks section: Select Webhooks version 7
    * Set Webhook callback URL to https://local-streaks-with-todoist.serveo.net/webhook_callback
    * Check the fields for item:added, item:complete, item:updated, reminder:fired
    * Click Save webhook configurations


### Local Installation

1. Clone the repo: `git clone https://github.com/briankaemingk/streaks-with-todoist.git`
2. Create the virtualenv
    ```
    $ virtualenv -p python3 venv  
    $ source .venv/bin/activate
    ```
3. Install the requirement packages:  `$ pip3 install -r requirements.txt`
4. Initiate the database:
    ```
    $ flask db init
    $ flask db migrate
    $ flask db upgrade 
    ```
5. Create an empty file called `.env` and copy and paste the example from the file `.env-example`, changing the CLIENT_ID and CLIENT_SECRET:
    * Log into the [Todoist app console](https://developer.todoist.com/appconsole.html) to add the client id and client secret:
    ```
    CLIENT_ID=...jfdk34s...
    CLIENT_SECRET=...343j...
    ```    
6. Start a tunnel using serveo: `ssh -R local-swt:80:localhost:5000 serveo.net` 
7. Start the redis server with: `rq worker swt-tasks` (don't forget to start ssh with `sudo service ssh start`, postgresql with `sudo service postgresql start`, and redis with `sudo service redis-server start` )
7. Run the app locally using `flask run`

### Staging Installation

1. Create a heroku app for your staging app: `$ heroku create staging-appname`
2. Create a new todoist account for your staging app and copy the client id and client secret from the [Todoist app console](https://developer.todoist.com/appconsole.html) (like in local installation step #5) and set them as variables in your staging app:
    ```
    $ heroku config:set CLIENT_ID=...jfdk34s...
    $ heroku config:set CLIENT_SECRET=...343j...
    ```
3. In addition, set the APP_SETTINGS variable: `heroku config:set APP_SETTINGS=config.StagingConfig`
4. Add the database add-on in heroku: `heroku addons:add heroku-postgresql:hobby-dev`
5. Push the app: `git push heroku master`
6. Log into the  Log into the [Todoist app console](https://developer.todoist.com/appconsole.html):
    * Change the OAuth redirect URL to your heroku app url: https://heroku_app_name.herokuapp.com/oauth_callback
    * Click Save Settings
    * Scroll down to the Webhooks section and set the Webhook callback URL to your heroku app url: https://heroku_app_name.herokuapp.com/webhook_callback
    * Click Save webhook configurations
    
### Database updates
If you make any updates to the database, you need to upgrade the database in your local and staging environments like this:

* Local: `$ flask db upgrade`  
* Staging: `$ heroku run flask db upgrade`
    * Running a command: `heroku pg:psql -c "command"`
You can access the database locally with the following commands:
```
$ sudo -u postgres psql
$ \c swt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
