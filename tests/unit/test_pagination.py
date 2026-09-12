# Team member: Prajval Sudhir (@prajvalsudhir)

from app.utils.pagination import parse_link_header


def test_parses_github_link_header() -> None:
    header = '<https://api.github.com/issues?page=2>; rel="next", <https://api.github.com/issues?page=4>; rel="last"'

    assert parse_link_header(header) == {
        "next": "https://api.github.com/issues?page=2",
        "last": "https://api.github.com/issues?page=4",
    }
