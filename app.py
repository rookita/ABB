from flask import redirect, render_template, session, url_for

from __init__ import app,scheduler
from config import host, port, debug
import auction

@app.route("/")
def index():
    if session.get('username') == None:
        return redirect(url_for("login"))
    return render_template("index.html")
@app.route("/base")
def base():
    return render_template("base.html")

if __name__ == "__main__":
    
    app.logger.info(f"starting server at {host}:{port} (debug={debug})")
    scheduler.start()
    app.run(host=host, port=port, debug=debug)