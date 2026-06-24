import csv
import html
import json
import re
import time
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LABELS = [
    "evidence_based_guidance",
    "implementation_question",
    "unsupported_claim",
    "showcase_reaction",
]

TARGET_PER_LABEL = 50
OUT_PATH = Path("data/annotated_examples.csv")


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def strip_html(value):
    if not value:
        return ""
    parser = HTMLStripper()
    parser.feed(html.unescape(value))
    text = parser.get_text()
    return clean_text(text)


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_json(url):
    req = Request(url, headers={"User-Agent": "AI201-TakeMeter-dataset-collector/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def add_row(rows, seen, text, label, source, source_url, reason, author=""):
    text = clean_text(text)
    if len(text) < 35 or len(text) > 900:
        return
    key = re.sub(r"\W+", "", text.lower())[:220]
    if key in seen:
        return
    seen.add(key)
    rows.append({
        "text": text,
        "label": label,
        "source": source,
        "source_url": source_url,
        "author": clean_text(author),
        "label_reason": reason,
    })


def stackexchange_url(endpoint, **params):
    base = f"https://api.stackexchange.com/2.3/{endpoint}"
    defaults = {
        "site": "raspberrypi",
        "pagesize": 100,
        "order": "desc",
        "sort": "votes",
        "filter": "withbody",
    }
    defaults.update(params)
    return base + "?" + urlencode(defaults)


def collect_stackexchange(rows, seen):
    for page in range(1, 5):
        data = get_json(stackexchange_url("questions", page=page))
        for item in data.get("items", []):
            title = strip_html(item.get("title", ""))
            body = strip_html(item.get("body", ""))
            text = f"{title} {body}"
            add_row(
                rows,
                seen,
                text,
                "implementation_question",
                "Raspberry Pi Stack Exchange question",
                item.get("link", ""),
                "Question post with concrete implementation context.",
                item.get("owner", {}).get("display_name", ""),
            )
        time.sleep(0.25)

    for page in range(1, 5):
        data = get_json(stackexchange_url("answers", page=page))
        for item in data.get("items", []):
            body = strip_html(item.get("body", ""))
            answer_id = item.get("answer_id", "")
            link = f"https://raspberrypi.stackexchange.com/a/{answer_id}" if answer_id else ""
            add_row(
                rows,
                seen,
                body,
                "evidence_based_guidance",
                "Raspberry Pi Stack Exchange answer",
                link,
                "Answer post with technical guidance or troubleshooting steps.",
                item.get("owner", {}).get("display_name", ""),
            )
        time.sleep(0.25)


def hn_url(query, tags, page):
    return "https://hn.algolia.com/api/v1/search?" + urlencode({
        "query": query,
        "tags": tags,
        "hitsPerPage": 100,
        "page": page,
    })


QUESTION_WORDS = re.compile(r"\b(how|what|why|where|can|could|should|does|do|is|are|anyone|help)\b", re.I)
GUIDANCE_WORDS = re.compile(r"\b(use|try|need|needs|because|if|configure|install|connect|measure|voltage|gpio|ssh|spi|i2c|pwm|driver|kernel|power supply|ground|resistor|mosfet)\b", re.I)
CLAIM_WORDS = re.compile(
    r"\b(best|worst|terrible|useless|overkill|no reason|nothing but|all you need|"
    r"obviously|ridiculous|pointless|garbage|sucks|better than|worse than|"
    r"should just|just use|never use|always use|never need|always need)\b",
    re.I,
)
SOFT_REACTION_WORDS = re.compile(r"\b(thanks|awesome|cool|nice|neat|love|interesting|congrats|great interview)\b", re.I)
REACTION_WORDS = re.compile(r"\b(cool|nice|neat|love|great|awesome|interesting|impressive|congrats|beautiful|fun|thanks for sharing|built|made|project)\b", re.I)


def classify_hn_text(text, is_story=False):
    lowered = text.lower()
    if is_story and (lowered.startswith("show hn") or re.search(r"\b(i built|i made|built a|made a|project)\b", lowered)):
        return "showcase_reaction", "HN story/project announcement."
    if "?" in text and QUESTION_WORDS.search(text):
        return "implementation_question", "Question-like community post."
    if CLAIM_WORDS.search(text) and not SOFT_REACTION_WORDS.search(text):
        return "unsupported_claim", "Broad or confident claim without enough detail in the post text."
    if GUIDANCE_WORDS.search(text) and len(text) > 90:
        return "evidence_based_guidance", "Contains actionable technical terms or advice."
    if REACTION_WORDS.search(text) and len(text) < 320:
        return "showcase_reaction", "Short project reaction or lightweight response."
    return None, None


def collect_hn(rows, seen):
    queries = [
        "raspberry pi",
        "arduino",
        "esp32",
        "microcontroller",
        "gpio",
        "robotics",
        "home automation",
        "embedded linux",
        "3d printer",
        "maker project",
    ]
    for query in queries:
        for tags in ["comment", "story"]:
            for page in range(0, 4):
                data = get_json(hn_url(query, tags, page))
                for hit in data.get("hits", []):
                    is_story = tags == "story"
                    raw = hit.get("title") if is_story else hit.get("comment_text")
                    text = strip_html(raw)
                    label, reason = classify_hn_text(text, is_story=is_story)
                    if not label:
                        continue
                    object_id = hit.get("objectID") or hit.get("story_id") or ""
                    source_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
                    add_row(
                        rows,
                        seen,
                        text,
                        label,
                        "Hacker News Algolia",
                        source_url,
                        reason,
                        hit.get("author", ""),
                    )
                time.sleep(0.15)


def select_balanced(rows):
    buckets = defaultdict(list)
    for row in rows:
        buckets[row["label"]].append(row)

    selected = []
    for label in LABELS:
        selected.extend(buckets[label][:TARGET_PER_LABEL])
    return selected, {label: len(buckets[label]) for label in LABELS}


def main():
    rows = []
    seen = set()
    collect_stackexchange(rows, seen)
    collect_hn(rows, seen)
    selected, available = select_balanced(rows)
    counts = Counter(row["label"] for row in selected)

    missing = [label for label in LABELS if counts[label] < TARGET_PER_LABEL]
    if missing:
        raise RuntimeError(f"Not enough examples for {missing}. Available: {available}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["text", "label", "source", "source_url", "author", "label_reason"],
        )
        writer.writeheader()
        writer.writerows(selected)

    print(f"Wrote {len(selected)} rows to {OUT_PATH}")
    print(dict(counts))
    print("Available before balancing:", available)


if __name__ == "__main__":
    main()
