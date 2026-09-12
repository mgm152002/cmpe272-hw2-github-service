# Team member: Prajval Sudhir (@prajvalsudhir)

def parse_link_header(value: str | None) -> dict[str, str]:
    links: dict[str, str] = {}
    if not value:
        return links
    for part in value.split(","):
        sections = [section.strip() for section in part.split(";")]
        if len(sections) < 2:
            continue
        url = sections[0].strip("<>")
        relation = sections[1].removeprefix('rel="').removesuffix('"')
        links[relation] = url
    return links
