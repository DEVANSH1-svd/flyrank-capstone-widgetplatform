import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_LENGTH = {"text": 255, "email": 254, "textarea": 2000}


class SubmissionValidationError(Exception):
    def __init__(self, errors: list[dict]):
        super().__init__("Submission validation failed")
        self.errors = errors


def validate_submission(widget_fields: list[dict], data: dict[str, str]) -> dict[str, str]:
    """Check visitor input against the widget's declared fields; return cleaned data."""
    errors = []
    declared = {field["name"]: field for field in widget_fields}

    for name in data:
        if name not in declared:
            errors.append({"field": name, "msg": "Unknown field"})

    cleaned = {}
    for name, field in declared.items():
        value = data.get(name, "").strip()
        if not value:
            if field["required"]:
                errors.append({"field": name, "msg": "This field is required"})
            continue
        if len(value) > MAX_LENGTH[field["type"]]:
            errors.append({"field": name, "msg": "Value is too long"})
        elif field["type"] == "email" and not EMAIL_PATTERN.match(value):
            errors.append({"field": name, "msg": "Invalid email address"})
        else:
            cleaned[name] = value

    if errors:
        raise SubmissionValidationError(errors)
    return cleaned