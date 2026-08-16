from flask import Flask, request
import db
import config

flask_app = Flask(__name__)


@flask_app.route("/adsgram-reward", methods=["GET"])
def adsgram_reward():
    """AdsGram calls this URL when a user finishes watching an ad."""
    tgid = request.args.get("tgid") or request.args.get("user_id") or request.args.get("telegram_id")
    if not tgid:
        return "missing tgid", 400
    try:
        user_id = int(tgid)
    except ValueError:
        return "invalid tgid", 400

    if db.get_user(user_id):
        db.add_points(user_id, config.POINTS_AD_VIEW)

    return "OK", 200


@flask_app.route("/")
def health():
    return "Bot webhook server is running", 200
