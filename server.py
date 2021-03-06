"""File that deals with server for Mindful Mornings site."""

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash,
                   session)
from flask_debugtoolbar import DebugToolbarExtension
from model import *  # import everything from model.py

app = Flask(__name__)  # this is the instance of the flask application

app.secret_key = "ABC"  # Required to use Flask sessions and debug toolbar

app.jinja_env.undefined = StrictUndefined  # Raises error for undefined vars

# Routes here #############################################################


@app.route("/")
def show_index():
    """Show homepage."""

    if session['user']:
        user_id = session['user']
        user = User.query.get(user_id)
        if user:
            username = user.username

    else:
        username = "friend"

    return render_template("index.html", username=username)


@app.route("/register", methods=["GET"])
def display_registration_form():
    """Display registration form for a new user."""

    return render_template("registration_form.html")


@app.route("/register", methods=["POST"])
def execute_user_registration():
    """Add new user to database using info provided in registration form."""

    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if password != confirm_password:
        flash("Your passwords do not match. Please try again.")
        return redirect("/register")

    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()

    user_id = user.user_id  # get new user's user_id (automatically generated)

    settings = Setting.query.all()  # list of all settings objects

    for setting in settings:  # going from Settings object -> UserSetting
        new_user_setting = UserSetting(user_id=user_id,
                                       setting_id=setting.setting_id,
                                       value=setting.setting_default_value)
        db.session.add(new_user_setting)
        db.session.commit()

    flash("Thank you for registering! Now please login with your credentials.")

    return redirect('/')


@app.route("/login", methods=["POST"])
def check_login_credentials():
    """Check user email and password against the db, add user to session."""

    username = request.form.get("username")  # get username from form
    password = request.form.get("password")  # get password from form
    user = User.query.filter_by(username=username).first()  # queries database

    if user:  # if the user exists (if that username exists)
        if user.password == password:  # check if the password is the same
            session['user'] = user.user_id  # adds user to the session

            flash("You are now logged in.")
            return redirect("/")
        else:
            flash("Incorrect login information. Please try again.")
            return redirect("/")

    elif not user:
        flash("Your username does not exist. Please try again or register as a new user.")
        return redirect("/")

    return render_template("index.html", username=username, password=password,
                           user=user)


@app.route("/logout")
def log_out_user():
    """Log user out."""

    session['user'] = None  # clears the user's data from the session
    flash("You are now logged out.")

    return redirect("/")


@app.route("/api/tasks", methods=["GET"])
def task_list():
    """Show list of tasks."""  # All task objects for this user

    user_id = session['user']  # get the user_id from the session dictionary
    tasks = Task.query.filter_by(user_id=user_id).all()  # get list of tasks

    return render_template("dashboard.html", tasks=tasks)


@app.route("/api/task", methods=["POST"])
def add_new_task():
    """Add a new task to user's task list."""

    user_id = session['user']  # get the user_id from the session dictionary
    task_name = request.form.get("task_name")  # get from the form
    duration_estimate = request.form.get("duration_estimate")  # get from form
    new_task = Task(user_id=user_id, task_name=task_name,
                    duration_estimate=duration_estimate)  # instantiate a Task

    db.session.add(new_task)  # add new task object to user's list of tasks
    db.session.commit()

    return redirect("/dashboard")  # go back to dashboard


@app.route("/api/task/<task_id>", methods=["GET", "DELETE"])
def delete_task_from_task_list(task_id):
    """Delete a task from user's task list."""

    try:
        task_to_delete = Task.query.get(task_id)  # get the task object to delete
        db.session.delete(task_to_delete)  # delete from database/task table
        db.session.commit()

    except AssertionError:
        flash("That task is active in your gameplan! Remove that task from gameplan before deleting from templates.")

    return redirect("/dashboard")  # go back to dashboard


@app.route("/settings", methods=["GET"])
def show_user_settings():
    """Show user's settings."""

    if session['user']:
        user_id = session['user']  # get the user_id from the session
        user = User.query.get(user_id)  # use the user_id to get the user
        username = user.username  # get the username from the user object
        user_settings = UserSetting.query.filter_by(user_id=user_id).order_by(UserSetting.user_setting_id).all()
    else:
        return redirect("/")

    return render_template("user_settings.html", username=username,
                           user_settings=user_settings)


@app.route("/api/setting/<user_setting_id>", methods=["GET","PUT"])
def update_user_setting(user_setting_id):
    """Update a setting for a user."""

    new_value_user_setting = request.values.get(user_setting_id)  # get from form
    user_setting = UserSetting.query.filter_by(user_setting_id=user_setting_id).one()  # get the user setting object
    user_setting.value = new_value_user_setting  # update setting w new value

    db.session.commit()

    return redirect("/settings")


@app.route("/dashboard", methods=["GET"])
def show_user_tasks_and_gameplan():
    """Show user's task templates and morning gameplan."""

    user_id = session['user']  # get the user_id from the session dictionary
    user = User.query.get(user_id)  # use the user_id to get the user object
    username = user.username  # get the username from the user object

    gameplan_tasks = GameplanTask.query.filter_by(user_id=user_id).order_by(GameplanTask.order).all()
    tasks = Task.query.filter_by(user_id=user_id).all()

    priority_object = UserSetting.query.filter_by(user_id=user_id,
                                                  setting_id=1).first()
    if priority_object:
        priority = priority_object.value
    else:
        priority = None

    intention_object = UserSetting.query.filter_by(user_id=user_id,
                                                   setting_id=9).first()
    if intention_object:
        intention = intention_object.value
    else:
        intention = None

    notes_reminders_object = UserSetting.query.filter_by(user_id=user_id,
                                                         setting_id=10).first()
    if notes_reminders_object:
        notes_reminders = notes_reminders_object.value
    else:
        notes_reminders = None

    return render_template("dashboard.html", username=username,
                           gameplan_tasks=gameplan_tasks, tasks=tasks,
                           priority=priority, intention=intention,
                           notes_reminders=notes_reminders)


@app.route("/api/add_task_to_gameplan", methods=["POST"])
def add_task_to_gameplan():
    """Add a task to user's gameplan."""
    # add a task to gameplan using a task template

    user_id = session['user']  # get the user_id from the session
    task_id = request.form.get("gameplan_task_name")  # get from the drop down
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    order = request.form.get("order")
    order = int(order)

    new_gameplan_task = GameplanTask(task_id=task_id, user_id=user_id,
                                     order=order, start_time=start_time,
                                     end_time=end_time)
    db.session.add(new_gameplan_task)
    db.session.commit()

    return redirect("/dashboard")


@app.route("/api/gptask/<task_id>", methods=["GET", "DELETE"])
def delete_task_from_gameplan(task_id):
    """Delete a task from user's active gameplan."""

    gptask_to_delete = GameplanTask.query.get(task_id)  # get the object
    db.session.delete(gptask_to_delete)  # delete from database/task table
    db.session.commit()

    return redirect("/dashboard")  # go back to dashboard


@app.route("/about")
def display_about_page():
    """Display about page."""

    return render_template("about.html")


if __name__ == "__main__":
    # set debug to true since it has to be true at the point
    # where we invoke the DebugToolbarExtension
    app.debug = True

    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the debug toolbar
    # DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
