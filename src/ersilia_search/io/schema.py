"""Field-name contract for the raw models.json records."""

# snake_case query-param name  ->  raw JSON key
PARAM_TO_RAW = {
    "task": "Task",
    "subtask": "Subtask",
    "tag": "Tag",
    "status": "Status",
    "biomedical_area": "Biomedical Area",
    "target_organism": "Target Organism",
}

# raw JSON key  ->  snake_case (handy for normalizing records / building responses)
RAW_TO_PARAM = {raw: param for param, raw in PARAM_TO_RAW.items()}

# How each field participates in search.
FIELD_GROUPS = {
    "free_text": ["Title", "Description", "Interpretation"],
    "single": ["Task", "Subtask", "Status"],
    "multi": [
        "Tag",
        "Biomedical Area",
        "Target Organism",
    ],
    "identifier": ["Identifier", "Slug", "Title"],
}
