from flask import Flask, redirect, request, session
from flask import render_template
from flaskwebgui import FlaskUI
import waitress

from src.manager import Manager

import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.DEBUG)

app = Flask(__name__)


manager = Manager(
    modules=[
        # Display string, module name, class name
        ("Biscuit", "biscuit", "Biscuit"),
        ("HDV Filter", "hdv_filter", "HDVFilter"),
        ("Team Manager", "team_manager", "TeamManager"),
        ("Forgemager", "forgemager", "Forgemager"),
        ("Treasure Hunter", "treasure_hunter", "TreasureHunter"),
        ("Debug", "debug", "Debug"),
    ],
)
module = None


@app.route("/")
def index():
    if manager.stop is not None:
        manager.stop()
    return render_template("index.html", modules=manager.modules, type=manager.type)


@app.route("/team_manager")
def team_manager():
    return render_template(
        "team_manager.html", team=module.get_team(), hash=module.__hash__()
    )


@app.route("/biscuit")
def biscuit():
    return render_template(
        "biscuit.html",
        config=module.config,
        houses=module.houses,
    )


@app.route("/debug")
def debug():
    return render_template(
        "debug.html",
    )


@app.route("/treasure_hunter")
def treasure_hunter():
    return render_template("treasure_hunter.html", config=module.get_config())


@app.route("/forgemager")
def forgemager():
    name, reliquat, level = module.get_item()
    return render_template(
        "forgemager.html",
        name=name,
        reliquat=reliquat,
        level=level,
    )


@app.route("/load", methods=["GET", "POST"])
def load():
    global module, manager
    if request.method == "POST":
        module = request.form["module"]
        class_name = request.form["class_name"]
        manager.set_current_module(module, class_name)
        module = manager.current_module
        manager.run()
    return {"status": "ok"}


@app.route("/team_update", methods=["GET", "POST"])
def team_update():
    if request.method == "POST":
        return {"hash": module.__hash__()}


@app.route("/hdv_filter_bid/<int:index>")
def hdv_filter_bid(index):
    effects, price = module.get_bid(index)
    return render_template(
        "hdv_filter_bid.html",
        effects=effects,
        price=price,
        name=module.item["name"],
        level=module.item["level"],
        index=index,
        total=len(module.releventBids),
        settings=session,
    )


@app.route("/hdv_filter")
def hdv_filter():
    if "negative" not in session:
        session["negative"] = "false"
    if module.item is not None:
        return render_template(
            "hdv_filter.html",
            content=module.item["effects"],
            filter_values=module.filter,
            name=module.item["name"],
            level=module.item["level"],
        )
    else:
        return render_template(
            "hdv_filter.html",
            content=[],
        )


@app.route("/hdv_filter_data", methods=["GET", "POST"])
def hdv_filter_data():
    if request.method == "POST":
        if "name" in request.form:
            name = request.form["name"]
            if module.item is not None and name != module.item["name"]:
                return {
                    "new_data": True,
                }
            else:
                return {
                    "new_data": False,
                }
        else:
            module.filterBids(request.form)
            return redirect("/hdv_filter_bid/0")
    return {"status": "ok"}


@app.route("/session_update", methods=["GET", "POST"])
def session_update():
    if request.method == "POST":
        for key in request.form:
            session[key] = request.form[key]
    return {"status": "ok"}


@app.route("/update", methods=["GET", "POST"])
def update():
    if request.method == "POST":
        data = request.form["data"]
        module.update(data)
    return "ok"


@app.route("/refresh", methods=["GET"])
def refresh():
    if request.method == "GET":
        data = module.get_data()
        return data
    return "ok"


@app.route("/switch_type", methods=["GET", "POST"])
def switch_type():
    if request.method == "POST":
        manager.switch_type()
    return "ok"


def start_flask(**server_kwargs):
    app = server_kwargs.pop("app", None)
    server_kwargs.pop("debug", None)

    waitress.serve(app, **server_kwargs)


if __name__ == "__main__":
    # If you are debugging you can do that in the browser:
    app.secret_key = "4f876ab4493c98f6e241355c57136259"
    app.config.update(TEMPLATES_AUTO_RELOAD=True, SESSION_TYPE="filesystem")
    # start_flask(app=app)
    # If you want to view the flaskwebgui window:
    # FlaskUI(app=app, server="flask", width=600, height=700).run()

    FlaskUI(
        server=start_flask,
        server_kwargs={
            "app": app,
            "port": 3000,
        },
        width=500,
        height=450,
        browser_path="C:\Program Files\Google\Chrome\Application\chrome.exe",
    ).run()
