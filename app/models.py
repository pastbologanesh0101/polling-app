"""Data access helpers for polls and options.

Kept as plain functions around sqlite3 rather than an ORM so the whole
app stays dependency-light (just Flask + the standard library).
"""

from app.db import get_db


class PollError(ValueError):
    """Raised when a poll cannot be created as requested."""


def create_poll(question, options):
    """Create a poll with the given question and option texts.

    Requires at least 2 non-empty options. Returns the new poll id.
    """
    question = (question or "").strip()
    cleaned_options = [o.strip() for o in options if o and o.strip()]

    if not question:
        raise PollError("A poll question is required.")
    if len(cleaned_options) < 2:
        raise PollError("A poll needs at least 2 options.")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO poll (question) VALUES (?)", (question,)
    )
    poll_id = cursor.lastrowid
    db.executemany(
        "INSERT INTO option (poll_id, text, vote_count) VALUES (?, ?, 0)",
        [(poll_id, text) for text in cleaned_options],
    )
    db.commit()
    return poll_id


def list_polls():
    """Return all polls, newest first, each with its options."""
    db = get_db()
    polls = db.execute(
        "SELECT id, question, created_at FROM poll ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return [get_poll(p["id"]) for p in polls]


def get_poll(poll_id):
    """Return a poll dict with its options and computed percentages, or None."""
    db = get_db()
    poll = db.execute(
        "SELECT id, question, created_at FROM poll WHERE id = ?", (poll_id,)
    ).fetchone()
    if poll is None:
        return None

    options = db.execute(
        "SELECT id, poll_id, text, vote_count FROM option WHERE poll_id = ? ORDER BY id",
        (poll_id,),
    ).fetchall()

    total_votes = sum(o["vote_count"] for o in options)

    option_list = []
    for o in options:
        percentage = (o["vote_count"] / total_votes * 100) if total_votes else 0.0
        option_list.append(
            {
                "id": o["id"],
                "poll_id": o["poll_id"],
                "text": o["text"],
                "vote_count": o["vote_count"],
                "percentage": round(percentage, 1),
            }
        )

    return {
        "id": poll["id"],
        "question": poll["question"],
        "created_at": poll["created_at"],
        "options": option_list,
        "total_votes": total_votes,
    }


def get_option(option_id):
    db = get_db()
    return db.execute(
        "SELECT id, poll_id, text, vote_count FROM option WHERE id = ?", (option_id,)
    ).fetchone()


def cast_vote(poll_id, option_id):
    """Increment the vote count for the given option on the given poll.

    Returns True if the vote was recorded, False if the option does not
    belong to the given poll (or does not exist).
    """
    db = get_db()
    option = db.execute(
        "SELECT id FROM option WHERE id = ? AND poll_id = ?", (option_id, poll_id)
    ).fetchone()
    if option is None:
        return False

    db.execute(
        "UPDATE option SET vote_count = vote_count + 1 WHERE id = ?", (option_id,)
    )
    db.commit()
    return True
