# Streaks with Todoist 
Enhancements to native behavior in todoist to improve motivation, focus, and flow.

## Installation

Visit [SwT homepage](https://streaks-with-todoist.herokuapp.com) to enable this integration.

## Improve Focus

### Just-In-Time Tasking
If you use todoist as your trusted system, then you inevitably have hundreds of tasks in your backlog at a given moment. How do you decide which of these tasks to do at a particular moment? 

JIT Tasking automates backlog filtering to only reveal tasks at the precise time, location, and context when they are actionable.

### Useage

JIT Tasking only shows you tasks when you are able to complete them. It accomplishes this through a combination of filtering and todoist api changes that run in the background.

1. Add a task scheduled for a particular day and time that you need to complete on that day, but aren't able to do them until a certain time. For example, let's say you need to make a personal phone call, but you don't want to make the call until after your shift at work ends at 6PM. Add that task in Todoist as `Call dad about birthday party` and set the due date as `today 6pm`.

2. Instead of looking at the default Today view in Todoist, look at a filter you will create called `Todo (Level 1)` which will hide this time-specific task until 6PM when you are able to do it. TODO: Automate filter creation

3. When 6PM rolls around, the due date for the task will be automatically changed to all-day today, and the task will automatically appear in your `Todo (Level 1)` filter.

### Recurrence Task Rescheduling (Premium Todoist users only)

Sometimes, your schedule requires you to postpone or reschedule repeating tasks. How do you properly postpone or reschedule a recurring task to a date *and time* outside of the regular recurrence?

### Usage

Recurrence scheduling allows you to postpone or reschedule a recurring task to a specific date and time while keeping the task recurrence in-tact.

1. First off, if you need to only change the day of a recurrence, but not the time, you can do that with Todoist: to postpone a recurring task, use the [task scheduler](https://support.todoist.com/hc/articles/205325931) by right-clicking (Web, Windows, macOS) or swiping left (iOS, Android) and pick a new date from there

2. If you need to not only change the day of the recurrence, but also the time, first add the time you want to reschedule the task to in the task as `<12:00>` or just `<>` if you want to change it to an all-day task

3. Next, assuming you want to change the date as well, use the [task scheduler](https://support.todoist.com/hc/articles/205325931) by right-clicking (Web, Windows, macOS) or swiping left (iOS, Android) and pick a new date from there

4. Todoist will move the task to the particular day you re-schedule it to and in the background, todoist-morph re-schedules your task to your desired time then removes the inputted time from the task description

## Improve Motivation

An automation to enable habit tracking in todoist. 

It integrates Seinfield's "[Don't Break the Chain](https://lifehacker.com/281626/jerry-seinfelds-productivity-secret)" method into [todoist](http://todoist.com/). Once it's setup, you can forget about it and it works seamlessly.

This is a different flavor of the originally implemented [habitist](https://github.com/amitness/habitist). While habitist is focused on daily habits, habitist (streak) can be applied to habits of any recurrence time-frames (daily, weekly, monthly, etc).

## Useage

1. You add habits you want to form as task on todoist with a recurring schedule (could be any recurrence pattern (`every day`, `every week` or `every year`, for example)

2. Add `[streak 0]` to the task

3. When you complete the task, the `[streak 0]` will become `[streak 1]`

4. If you fail to complete the task and it becomes overdue, the script will schedule it to today and reset `[streak X]` to `[streak 0]`.

## Installing local copy

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
