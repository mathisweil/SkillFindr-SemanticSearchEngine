def build_combined_text(row: dict) -> str:
    """
    Constructs a combined text string from title, description, and tags.
    """
    title = row.get("title", "")
    description = row.get("description", "")
    tags = "; ".join(row.get("tags", []))
    if tags:
        return f"{title}. {description}. Tags: {tags}"
    return f"{title}. {description}"
