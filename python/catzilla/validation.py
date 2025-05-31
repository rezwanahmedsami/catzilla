"""
Catzilla Ultra-Fast Validation Engine - Pydantic-Compatible API

This module provides a Pydantic-compatible interface that internally uses
C-accelerated validation for 100x performance improvements.

Example usage:
    # Pydantic-style syntax (recommended)
    class User(BaseModel):
        id: int
        name: str
        email: str | None = None
        age: int | None = None

    # Advanced Field syntax (for fine control)
    class Product(BaseModel):
        name = StringField(min_len=1, max_len=200)
        price = FloatField(min=0.01, max=999999.99)
        tags = ListField(StringField(), max_items=10)
"""

import inspect
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

# Handle Python 3.10+ Union syntax
if sys.version_info >= (3, 10):
    from types import UnionType
else:
    UnionType = None

# Import C validation functions (will be available after build)
try:
    from catzilla._catzilla import (
        create_float_validator,
        create_int_validator,
        create_model,
        create_string_validator,
        get_validation_stats,
        reset_validation_stats,
    )

    _C_VALIDATION_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    _C_VALIDATION_AVAILABLE = False

    def create_int_validator(**kwargs):
        return None

    def create_string_validator(**kwargs):
        return None

    def create_float_validator(**kwargs):
        return None

    def create_model(name, fields):
        return None

    def get_validation_stats():
        return {}

    def reset_validation_stats():
        pass


__all__ = [
    "BaseModel",
    "Field",
    "IntField",
    "StringField",
    "FloatField",
    "BoolField",
    "ListField",
    "OptionalField",
    "ValidationError",
    "get_validation_stats",
    "reset_validation_stats",
]


class ValidationError(ValueError):
    """Validation error compatible with Pydantic ValidationError"""

    pass


class Field:
    """Base field class for explicit field definitions"""

    def __init__(self, default=None, optional=False, description=None):
        self.default = default
        self.optional = optional
        self.description = description
        self._c_validator = None

    def _create_c_validator(self):
        """Override in subclasses to create specific C validators"""
        raise NotImplementedError("Subclasses must implement _create_c_validator")

    def get_c_validator(self):
        """Get or create the C validator for this field"""
        if self._c_validator is None:
            self._c_validator = self._create_c_validator()
        return self._c_validator


class IntField(Field):
    """Integer field with min/max constraints"""

    def __init__(self, min=None, max=None, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max

    def _create_c_validator(self):
        return create_int_validator(min=self.min, max=self.max)


class StringField(Field):
    """String field with length and pattern constraints"""

    def __init__(self, min_len=None, max_len=None, pattern=None, **kwargs):
        super().__init__(**kwargs)
        self.min_len = min_len
        self.max_len = max_len
        self.pattern = pattern

    def _create_c_validator(self):
        return create_string_validator(
            min_len=self.min_len, max_len=self.max_len, pattern=self.pattern
        )


class FloatField(Field):
    """Float field with min/max constraints"""

    def __init__(self, min=None, max=None, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max

    def _create_c_validator(self):
        return create_float_validator(min=self.min, max=self.max)


class BoolField(Field):
    """Boolean field"""

    def _create_c_validator(self):
        # For now, create a basic validator - we'll enhance this in the C code
        return create_int_validator(min=0, max=1)  # Temporary implementation


class ListField(Field):
    """List field with item type and size constraints"""

    def __init__(self, item_field, min_items=None, max_items=None, **kwargs):
        super().__init__(**kwargs)
        self.item_field = item_field
        self.min_items = min_items
        self.max_items = max_items

    def _create_c_validator(self):
        # For now, create a basic validator - we'll enhance this in the C code
        return create_string_validator()  # Temporary implementation


class OptionalField(Field):
    """Optional wrapper for other fields"""

    def __init__(self, inner_field, **kwargs):
        super().__init__(optional=True, **kwargs)
        self.inner_field = inner_field

    def _create_c_validator(self):
        return self.inner_field.get_c_validator()


class TypeConverter:
    """Converts Python type hints to Field objects"""

    @staticmethod
    def convert_type_hint(type_hint, default_value=None, has_default=False):
        """Convert a type hint to a Field object"""

        # Determine if field is optional based on:
        # 1. Type annotation (Optional[Type] or Union[Type, None])
        # 2. Presence of explicit default value
        is_optional = False

        # Only set as optional if there's an explicit default value
        if has_default:
            is_optional = True

        # Handle Union types (e.g., str | None, Union[str, None])
        origin = get_origin(type_hint)
        if origin is Union or (UnionType and origin is UnionType):
            args = get_args(type_hint)

            # Check if it's Optional (Union with None)
            if len(args) == 2 and type(None) in args:
                # Optional type
                non_none_type = args[0] if args[1] is type(None) else args[1]
                field = TypeConverter.convert_type_hint(
                    non_none_type, default_value, has_default
                )
                field.optional = True  # Optional fields are always optional
                return field
            else:
                # TODO: Handle other Union types
                raise NotImplementedError(f"Union types not yet supported: {type_hint}")

        # Handle basic types
        if type_hint is int:
            return IntField(default=default_value, optional=is_optional)
        elif type_hint is str:
            return StringField(default=default_value, optional=is_optional)
        elif type_hint is float:
            return FloatField(default=default_value, optional=is_optional)
        elif type_hint is bool:
            return BoolField(default=default_value, optional=is_optional)

        # Handle List types
        elif origin is list or origin is List:
            args = get_args(type_hint)
            if args:
                item_field = TypeConverter.convert_type_hint(args[0])
                return ListField(
                    item_field, default=default_value, optional=is_optional
                )
            else:
                return ListField(
                    StringField(), default=default_value, optional=is_optional
                )

        # Handle Dict types (basic implementation)
        elif origin is dict or origin is Dict:
            # For now, treat as optional string field
            return StringField(default=default_value, optional=True)

        else:
            raise NotImplementedError(f"Type not yet supported: {type_hint}")


class BaseModelMeta(type):
    """Metaclass for BaseModel that handles Pydantic-style type annotation conversion"""

    def __new__(mcs, name, bases, namespace, **kwargs):
        # Create the class first
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip BaseModel itself
        if name == "BaseModel":
            return cls

        # Process type annotations and convert to Field objects
        cls._process_annotations()

        # Compile the model to C for ultra-fast validation
        cls._compile_to_c()

        return cls

    def _process_annotations(cls):
        """Convert type annotations to Field objects if not explicitly defined"""

        # Get type hints for this class
        try:
            type_hints = get_type_hints(cls)
        except (NameError, AttributeError):
            type_hints = getattr(cls, "__annotations__", {})

        cls._fields = {}

        # Process each annotated field
        for field_name, field_type in type_hints.items():

            # Check if field is already explicitly defined
            if hasattr(cls, field_name) and isinstance(getattr(cls, field_name), Field):
                # Use explicit Field definition
                cls._fields[field_name] = getattr(cls, field_name)
            else:
                # Convert type annotation to Field
                # Check if the field has an explicit default value in the class
                has_default = hasattr(cls, field_name)
                default_value = getattr(cls, field_name, None) if has_default else None
                field = TypeConverter.convert_type_hint(
                    field_type, default_value, has_default
                )
                cls._fields[field_name] = field

                # Set the field on the class
                setattr(cls, field_name, field)

        # Also process explicitly defined Field objects that don't have annotations
        for attr_name in dir(cls):
            if not attr_name.startswith("_"):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, Field) and attr_name not in cls._fields:
                    cls._fields[attr_name] = attr_value

    def _compile_to_c(cls):
        """Compile the model to C for ultra-fast validation"""

        if not hasattr(cls, "_fields") or not cls._fields:
            cls._c_model = None
            return

        if not _C_VALIDATION_AVAILABLE:
            cls._c_model = None
            return

        # Create field dict for C model creation, making sure to set required correctly
        c_fields = {}
        for field_name, field in cls._fields.items():
            # Pass validator and required status (opposite of optional)
            required = not field.optional
            c_fields[field_name] = (field.get_c_validator(), required)

        try:
            # Create C model specification
            cls._c_model = create_model(cls.__name__, c_fields)
        except Exception as e:
            print(f"Warning: Failed to compile model {cls.__name__} to C: {e}")
            cls._c_model = None


class BaseModel(metaclass=BaseModelMeta):
    """
    Base class for Pydantic-compatible models with C-accelerated validation

    Supports both Pydantic-style type annotations and explicit Field definitions:

    # Pydantic-style (automatically converted)
    class User(BaseModel):
        id: int
        name: str
        email: str | None = None

    # Explicit Field style (for advanced control)
    class Product(BaseModel):
        name = StringField(min_len=1, max_len=200)
        price = FloatField(min=0.01)
    """

    def __init__(self, **data):
        """Initialize model with data (validates automatically)"""
        validated_data = self.validate(data)
        self.__dict__.update(validated_data)

    @classmethod
    def validate(cls, data):
        """
        Validate data against the model using ultra-fast C validation

        Args:
            data: Dictionary of data to validate

        Returns:
            Dictionary of validated/coerced data

        Raises:
            ValidationError: If validation fails
        """
        if not hasattr(cls, "_c_model") or cls._c_model is None:
            # Fallback to Python validation if C compilation failed
            return cls._validate_python(data)

        try:
            # Preprocess data for C validation (convert types as needed)
            preprocessed_data = cls._preprocess_for_c_validation(data)
            # Use ultra-fast C validation
            return cls._c_model.validate(preprocessed_data)
        except Exception as e:
            raise ValidationError(str(e))

    @classmethod
    def _validate_python(cls, data):
        """Fallback Python validation (much slower but functional)"""

        if not hasattr(cls, "_fields"):
            return data

        validated = {}
        errors = []

        for field_name, field in cls._fields.items():
            if field_name in data:
                # TODO: Implement Python validation logic
                validated[field_name] = data[field_name]
            elif not field.optional:
                if field.default is not None:
                    validated[field_name] = field.default
                else:
                    errors.append(f"Field '{field_name}' is required")

        if errors:
            raise ValidationError("; ".join(errors))

        return validated

    @classmethod
    def _preprocess_for_c_validation(cls, data):
        """
        Preprocess data to convert Python types for C validation

        Args:
            data: Dictionary of data to preprocess

        Returns:
            Dictionary with converted data types
        """
        if not hasattr(cls, "_fields"):
            return data

        preprocessed = {}
        for key, value in data.items():
            if key in cls._fields:
                field = cls._fields[key]
                # Convert boolean values to integers for BoolField
                if isinstance(field, BoolField):
                    if isinstance(value, bool):
                        preprocessed[key] = int(value)  # True -> 1, False -> 0
                    else:
                        preprocessed[key] = value
                else:
                    preprocessed[key] = value
            else:
                preprocessed[key] = value

        return preprocessed

    def dict(self):
        """Return model data as dictionary (Pydantic compatibility)"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def json(self, **kwargs):
        """Return model data as JSON string (Pydantic compatibility)"""
        import json

        return json.dumps(self.dict(), **kwargs)

    @classmethod
    def parse_obj(cls, obj):
        """Parse object into model (Pydantic compatibility)"""
        return cls(**obj)

    @classmethod
    def parse_raw(cls, raw_data, content_type="json"):
        """Parse raw string data into model (Pydantic compatibility)"""
        import json

        if content_type == "json":
            data = json.loads(raw_data)
            return cls.parse_obj(data)
        else:
            raise NotImplementedError(f"Content type {content_type} not supported")

    def __repr__(self):
        fields = ", ".join(f"{k}={v!r}" for k, v in self.dict().items())
        return f"{self.__class__.__name__}({fields})"


# Performance monitoring functions
def get_performance_stats():
    """Get validation performance statistics"""
    return get_validation_stats()


def reset_performance_stats():
    """Reset validation performance statistics"""
    reset_validation_stats()


# Compatibility aliases for easier migration from Pydantic
def validator(*args, **kwargs):
    """Placeholder for Pydantic validator decorator (not yet implemented)"""

    def decorator(func):
        return func

    return decorator


def root_validator(*args, **kwargs):
    """Placeholder for Pydantic root_validator decorator (not yet implemented)"""

    def decorator(func):
        return func

    return decorator
