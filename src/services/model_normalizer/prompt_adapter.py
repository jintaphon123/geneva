from __future__ import annotations

import json


def adapt_tool_schemas(
    tool_schemas: list[dict],
    tier: str,
) -> list[dict]:
    """Augment tool schema descriptions for medium/weak models.

    Strong models return schemas unchanged. Medium/weak models get a compact
    JSON example appended to each tool description.
    """
    if tier == "strong":
        return tool_schemas

    adapted: list[dict] = []
    for schema in tool_schemas:
        input_schema = schema.get("input_schema", {})
        props: dict = input_schema.get("properties", {})
        if not props:
            adapted.append(schema)
            continue

        required: list[str] = [
            key for key in input_schema.get("required", []) if key in props
        ]
        example_keys = required[:3] or list(props.keys())[:3]
        example: dict = {}
        for key in example_keys:
            prop = props.get(key, {})
            if not isinstance(prop, dict):
                prop = {}
            ptype = prop.get("type", "string")
            if ptype == "string":
                example[key] = f"<{key}>"
            elif ptype == "integer":
                example[key] = 0
            elif ptype == "boolean":
                example[key] = True
            elif ptype == "array":
                example[key] = []
            else:
                example[key] = {}

        adapted_schema = dict(schema)
        adapted_schema["description"] = (
            schema.get("description", "")
            + f"\nExample input: {json.dumps(example, ensure_ascii=False)}"
        )
        adapted.append(adapted_schema)

    return adapted
