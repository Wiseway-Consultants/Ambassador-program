class ValidationError(Exception):
    pass


def validate_prospect(data):
    # Define expected fields and types
    schema = {
        "id": int,
        "number_of_frylows": int
    }

    # Check for unexpected fields
    extra_fields = set(data) - set(schema)
    if extra_fields:
        raise ValueError(f"Unexpected fields: {extra_fields}")

    # Check for missing fields
    missing_fields = set(schema) - set(data)
    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields}")

    # Validate types
    for field, expected_type in schema.items():
        value = data[field]
        if not isinstance(value, expected_type):
            raise TypeError(f"Field '{field}' must be of type {expected_type}, got {type(value)}")

    # Optional: validate email format
    if "@" not in data["email"]:
        raise ValueError("Invalid email format")

    return True  # Payload is valid
