from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models import PollError, cast_vote, create_poll, get_poll, list_polls

bp = Blueprint("polls", __name__)


def _voted_polls():
    return session.setdefault("voted_polls", [])


@bp.route("/")
def index():
    polls = list_polls()
    return render_template("index.html", polls=polls)


@bp.route("/poll/new", methods=["GET", "POST"])
def new_poll():
    if request.method == "POST":
        question = request.form.get("question", "")
        options = request.form.getlist("option")
        try:
            poll_id = create_poll(question, options)
        except PollError as exc:
            flash(str(exc))
            return render_template(
                "new_poll.html", question=question, options=options
            )
        return redirect(url_for("polls.view_poll", poll_id=poll_id))

    return render_template("new_poll.html", question="", options=["", ""])


@bp.route("/poll/<int:poll_id>")
def view_poll(poll_id):
    poll = get_poll(poll_id)
    if poll is None:
        abort(404)
    has_voted = poll_id in _voted_polls()
    return render_template("poll.html", poll=poll, has_voted=has_voted)


@bp.route("/poll/<int:poll_id>/vote", methods=["POST"])
def vote(poll_id):
    poll = get_poll(poll_id)
    if poll is None:
        abort(404)

    voted = _voted_polls()
    if poll_id in voted:
        flash("You have already voted on this poll.")
        return redirect(url_for("polls.view_poll", poll_id=poll_id))

    option_id = request.form.get("option_id", type=int)
    if option_id is None or not cast_vote(poll_id, option_id):
        flash("Please choose a valid option.")
        return redirect(url_for("polls.view_poll", poll_id=poll_id))

    voted.append(poll_id)
    session["voted_polls"] = voted
    session.modified = True

    return redirect(url_for("polls.view_poll", poll_id=poll_id))
