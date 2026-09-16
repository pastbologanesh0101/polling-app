import re


def _create_poll(client, question="Best language?", options=("Python", "JavaScript")):
    response = client.post(
        "/poll/new",
        data={"question": question, "option": list(options)},
        follow_redirects=False,
    )
    assert response.status_code == 302
    match = re.search(r"/poll/(\d+)$", response.headers["Location"])
    assert match, f"unexpected redirect location: {response.headers['Location']}"
    return int(match.group(1))


def test_create_poll(client):
    poll_id = _create_poll(client)
    response = client.get(f"/poll/{poll_id}")
    assert response.status_code == 200
    assert b"Best language?" in response.data
    assert b"Python" in response.data
    assert b"JavaScript" in response.data


def test_poll_with_too_few_options_is_rejected(client):
    response = client.post(
        "/poll/new",
        data={"question": "Only one option?", "option": ["Just this one"]},
        follow_redirects=True,
    )
    # No redirect to a poll page; the form is re-rendered with an error.
    assert response.status_code == 200
    assert b"at least 2 options" in response.data
    assert b"/poll/new" in response.request.path.encode() or response.request.path == "/poll/new"


def test_vote_increments_count(client):
    poll_id = _create_poll(client, options=("Cats", "Dogs"))
    poll_page = client.get(f"/poll/{poll_id}")
    option_id_match = re.search(rb'value="(\d+)"', poll_page.data)
    option_id = int(option_id_match.group(1))

    client.post(f"/poll/{poll_id}/vote", data={"option_id": option_id})

    response = client.get(f"/poll/{poll_id}")
    assert b"1 vote" in response.data


def test_percentages_computed_correctly(client):
    poll_id = _create_poll(client, options=("A", "B"))
    poll_page = client.get(f"/poll/{poll_id}")
    ids = [int(m) for m in re.findall(rb'value="(\d+)"', poll_page.data)]
    option_a, option_b = ids[0], ids[1]

    # Vote for A three times and B once using separate sessions so each
    # vote is allowed (one vote per session per poll).
    for _ in range(3):
        with client.session_transaction() as sess:
            sess.pop("voted_polls", None)
        client.post(f"/poll/{poll_id}/vote", data={"option_id": option_a})

    with client.session_transaction() as sess:
        sess.pop("voted_polls", None)
    client.post(f"/poll/{poll_id}/vote", data={"option_id": option_b})

    response = client.get(f"/poll/{poll_id}")
    assert b"75.0%" in response.data  # A: 3/4
    assert b"25.0%" in response.data  # B: 1/4


def test_double_vote_in_same_session_is_blocked(client):
    poll_id = _create_poll(client, options=("Tea", "Coffee"))
    poll_page = client.get(f"/poll/{poll_id}")
    option_id = int(re.search(rb'value="(\d+)"', poll_page.data).group(1))

    first = client.post(
        f"/poll/{poll_id}/vote", data={"option_id": option_id}, follow_redirects=True
    )
    assert b"1 vote" in first.data

    # Second vote attempt in the same session should be rejected.
    second = client.post(
        f"/poll/{poll_id}/vote", data={"option_id": option_id}, follow_redirects=True
    )
    assert b"already voted" in second.data
    assert b"1 vote" in second.data  # count did not increase to 2


def test_list_all_polls(client):
    _create_poll(client, question="Poll One", options=("X", "Y"))
    _create_poll(client, question="Poll Two", options=("M", "N"))

    response = client.get("/")
    assert response.status_code == 200
    assert b"Poll One" in response.data
    assert b"Poll Two" in response.data
