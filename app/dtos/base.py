from dataclasses import dataclass, fields


class DTOValidationError(Exception):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")


class BaseDTO:
    def __post_init__(self):
        errors = []

        for f in fields(self):
            value = getattr(self, f.name)

            if value is None:
                errors.append({"field": f.name, "message": f"{f.name} is required"})
                continue

            if not isinstance(value, str):
                errors.append({"field": f.name, "message": f"{f.name} must be a string"})
                continue

            value = value.strip()
            setattr(self, f.name, value)

            if not value:
                errors.append({"field": f.name, "message": f"{f.name} cannot be blank"})
                continue

            validator = getattr(self, f"_validate_{f.name}", None)
            if validator:
                message = validator(value)
                if message:
                    errors.append({"field": f.name, "message": message})


        if errors:
            raise DTOValidationError(errors)