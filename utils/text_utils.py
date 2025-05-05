def build_combined_text(row: dict) -> str:
    """
    Constructs a labelled, combined text string from title, description, and tags.
    Each non‐empty field is prefixed with its label and separated by a sentence boundary.
    """
    parts = []

    title = row.get("title", "").strip()
    if title:
        parts.append(f"title: {title}")

    description = row.get("description", "").strip()
    if description:
        parts.append(f"description: {description}")

    tags_list = row.get("tags", [])
    if tags_list:
        tags = ", ".join(tag.strip() for tag in tags_list if tag.strip())
        if tags:
            parts.append(f"tags: {tags}")

    if not parts:
        return ""

    combined = ". ".join(parts)
    if not combined.endswith("."):
        combined += "."

    return combined
