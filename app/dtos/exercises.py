import re
from dataclasses import dataclass, fields
from typing import Any, ClassVar
from urllib.parse import urlsplit

from bson import ObjectId

from app.dtos.base import DTOValidationError


MUSCLE_GROUPS = ('CHEST', 'BACK', 'LEGS', 'ARMS', 'SHOULDERS', 'CORE', 'FULL_BODY')
EQUIPMENT = ('BARBELL', 'DUMBBELL', 'MACHINE', 'BODYWEIGHT', 'KETTLEBELL', 'RESISTANCE_BAND', 'OTHER')
NAME_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 500
UNSET = object()
_ID_PATTERN = re.compile(r'[a-fA-F0-9]{24}')
_URI_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]*")
# Component character sets follow RFC 3986, Appendix A.
_URI_CHARS = r"A-Za-z0-9\-._~!$&'()*+,;="
_URI_PATH = re.compile(rf'[{_URI_CHARS}%:@/]*')
_URI_QUERY_FRAGMENT = re.compile(rf'[{_URI_CHARS}%:@/?]*')
_URI_AUTHORITY = re.compile(
    rf'(?:[{_URI_CHARS}%:]*@)?'
    rf'(?:\[(?:[a-fA-F0-9:.]+|[vV][a-fA-F0-9]+\.[{_URI_CHARS}:]+)\]|[{_URI_CHARS}%]*)'
    r'(?::[0-9]*)?'
)


def validate_exercise_id(value: str) -> ObjectId:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise DTOValidationError([{'field': 'exercise_id', 'message': 'exercise_id must be a 24-character hexadecimal string'}])
    return ObjectId(value)


def _array_error(name: str, value: Any, allowed: tuple[str, ...]) -> str | None:
    if not isinstance(value, list):
        return f'{name} must be an array'
    if not value:
        return f'{name} must contain at least 1 item'
    if any(not isinstance(item, str) or item not in allowed for item in value):
        return f'{name} must contain only allowed values: {", ".join(allowed)}'
    return None


def _valid_uri(value: str) -> bool:
    if not _URI_PATTERN.fullmatch(value) or re.search(r'%(?![a-fA-F0-9]{2})', value):
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return all((
        _URI_AUTHORITY.fullmatch(parts.netloc),
        _URI_PATH.fullmatch(parts.path),
        _URI_QUERY_FRAGMENT.fullmatch(parts.query),
        _URI_QUERY_FRAGMENT.fullmatch(parts.fragment),
    ))


@dataclass
class _ExerciseDTO:
    name: Any = UNSET
    description: Any = UNSET
    muscle_groups: Any = UNSET
    equipment: Any = UNSET
    video_url: Any = UNSET
    image_url: Any = UNSET
    required_fields: ClassVar[tuple[str, ...]] = ()

    def __post_init__(self):
        errors = []
        enums = {'muscle_groups': MUSCLE_GROUPS, 'equipment': EQUIPMENT}
        for item in fields(self):
            name = item.name
            value = getattr(self, name)
            if value is UNSET:
                if name in self.required_fields:
                    errors.append({'field': name, 'message': f'{name} is required'})
                continue
            allowed = enums.get(name)
            if allowed is not None:
                message = _array_error(name, value, allowed)
            elif not isinstance(value, str):
                message = f'{name} must be a string'
            elif name == 'name':
                value = value.strip()
                self.name = value
                message = 'name cannot be blank' if not value else (f'name must be at most {NAME_MAX_LENGTH} characters' if len(value) > NAME_MAX_LENGTH else None)
            elif name == 'description':
                message = f'description must be at most {DESCRIPTION_MAX_LENGTH} characters' if len(value) > DESCRIPTION_MAX_LENGTH else None
            else:
                message = None if _valid_uri(value) else f'{name} must be a valid URI'
            if message:
                errors.append({'field': name, 'message': message})
        if errors:
            raise DTOValidationError(errors)

    def to_document(self) -> dict:
        return {item.name: getattr(self, item.name) for item in fields(self) if getattr(self, item.name) is not UNSET}


@dataclass
class ExerciseCreateDTO(_ExerciseDTO):
    required_fields: ClassVar[tuple[str, ...]] = ('name', 'muscle_groups', 'equipment')


@dataclass
class ExerciseUpdateDTO(_ExerciseDTO):
    pass


@dataclass
class ExerciseListDTO:
    muscle_group: Any = None
    equipment: Any = None
    search: Any = None
    cursor: Any = None
    limit: Any = 20

    def __post_init__(self):
        errors = []
        for name, allowed in (('muscle_group', MUSCLE_GROUPS), ('equipment', EQUIPMENT)):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, str):
                errors.append({'field': name, 'message': f'{name} must be a comma-separated string'})
                continue
            values = [item.strip() for item in value.split(',')]
            message = _array_error(name, values, allowed)
            if message:
                errors.append({'field': name, 'message': message})
            else:
                setattr(self, name, values)
        if self.search is not None and not isinstance(self.search, str):
            errors.append({'field': 'search', 'message': 'search must be a string'})
        if self.cursor is not None:
            try:
                self.cursor = validate_exercise_id(self.cursor)
            except DTOValidationError:
                errors.append({'field': 'cursor', 'message': 'cursor must be a valid exercise cursor'})
        limit = self.limit
        if isinstance(limit, str) and limit.isascii() and limit.isdigit():
            digits = limit.lstrip('0') or '0'
            limit = int(digits) if len(digits) <= 3 else 101
        if type(limit) is not int or not 1 <= limit <= 100:
            errors.append({'field': 'limit', 'message': 'limit must be an integer between 1 and 100'})
        else:
            self.limit = limit
        if errors:
            raise DTOValidationError(errors)
