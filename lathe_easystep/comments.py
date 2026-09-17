"""Generated descriptions carry no persistent operation number."""
import re

_NUMBER = re.compile(r"^\d+\.\s+")


def is_generated_comment(comment):
    text = str(comment or "").strip()
    return not text or bool(_NUMBER.match(text))


def unnumbered_comment(comment):
    return _NUMBER.sub("", str(comment or "").strip(), count=1)


def update_auto_comment(op, description):
    if op.params.get("_auto_comment") or is_generated_comment(op.params.get("comment")):
        op.params["comment"] = unnumbered_comment(description)
        op.params["_auto_comment"] = True
