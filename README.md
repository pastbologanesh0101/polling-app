# Polling Website

A small Flask + SQLite polling app. Create polls with two or more options,
share the link, and let people vote — results are shown as live-computed
percentage bars, and each browser session can only vote once per poll.

## Features

- Create a poll with a question and 2+ options
- View a poll with live-computed vote percentages (rendered as simple CSS bars)
- Vote on an option, with double-voting on the same poll blocked via a
  signed session cookie (Flask's built-in signed session, no extra state
  needed on the server beyond the vote counts themselves)
- Browse a list of all polls

## Tech

- Flask (app factory pattern via `create_app()`)
- SQLite (accessed directly with the standard library `sqlite3` module —
  no ORM)
- Server-rendered Jinja2 templates + plain CSS (no JavaScript required)

## Project layout

```
polling-app/
├── app/
│   ├── __init__.py      # create_app() application factory
│   ├── db.py            # SQLite connection + schema management
│   ├── models.py        # poll/option data access functions
│   ├── routes.py        # Flask routes (blueprint)
│   ├── templates/       # Jinja2 templates
│   └── static/style.css # plain CSS
├── tests/               # pytest tests using Flask's test client
├── wsgi.py              # entry point for running the app
└── requirements.txt
```

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python wsgi.py
```

The app will be available at `http://127.0.0.1:5000/`. Data is stored in
`instance/polls.sqlite`, created automatically on first run.

## Example usage

1. Visit `/poll/new` and create a poll, e.g. question "Best language?"
   with options "Python" and "JavaScript".
2. You're redirected to `/poll/<id>`, showing the poll with a 0% bar for
   each option.
3. Pick an option and click "Vote". The bars update to reflect the new
   percentages (e.g. 100% / 0% after the first vote).
4. Reload the page or try to vote again — the app remembers (via your
   session cookie) that you already voted on this poll and blocks a
   second vote, showing "You have already voted on this poll."
5. Visit `/` to see every poll created so far, along with total vote counts.

## Running tests

```bash
pip install -r requirements.txt pytest
pytest -v
```

Tests use `create_app(testing=True)`, which points the app at a fresh
temporary SQLite database file per test, so they never touch real data.
Covered cases include: creating a poll, vote counts incrementing,
percentage calculation, blocking a double vote in the same session, and
rejecting a poll created with fewer than 2 options.

## Continuous integration

`.github/workflows/tests.yml` runs the full test suite on every push and
pull request against Python 3.11 and 3.12.

## License

MIT — see [LICENSE](LICENSE).
