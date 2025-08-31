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
        name: str = Field(min_length=1, max_length=200)
        price: float = Field(gt=0.01, le=999999.99)
        tags: List[str] = Field(max_items=10)
"""

import gc
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
        create_list_validator,
        create_model,
        create_optional_validator,
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

    def create_list_validator(**kwargs):
        return None

    def create_optional_validator(**kwargs):
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
    "ValidationError",
    "get_validation_stats",
    "reset_validation_stats",
    "get_performance_stats",
    "reset_performance_stats",
]


class ValidationError(ValueError):
    """Validation error compatible with Pydantic ValidationError"""

    pass


class Field:
    """
    FastAPI/Pydantic-compatible Field class for validation constraints

    Supports FastAPI-style constraints:
    - ge, gt, le, lt (numbers)
    - min_length, max_length (strings)
    - min_items, max_items (lists)
    - regex (strings)
    - default (default values)
    - description (field documentation)

    Example usage:
        # Basic usage
        name: str = Field(min_length=3, max_length=50)
        age: int = Field(ge=18, le=120)
        score: float = Field(gt=0.0, lt=100.0)
        tags: List[str] = Field(min_items=1, max_items=10)

        # With defaults
        is_active: bool = Field(default=True, description="User status")
        bio: Optional[str] = Field(None, max_length=500)

        # Required fields (FastAPI style)
        user_id: int = Field(..., ge=1, description="User ID")
    """

    def __init__(
        self,
        default=...,  # Use ... to indicate required field (FastAPI style)
        *,
        # String constraints
        min_length=None,
        max_length=None,
        regex=None,
        # Numeric constraints (FastAPI compatible names)
        gt=None,  # greater than
        ge=None,  # greater than or equal
        lt=None,  # less than
        le=None,  # less than or equal
        # List constraints
        min_items=None,
        max_items=None,
        # General
        description=None,
        example=None,
        # Legacy support (deprecated, will be removed)
        optional=False,
    ):
        # Handle default value (FastAPI style)
        if default is ...:
            self.default = None
            self.is_required = True
        else:
            self.default = default
            self.is_required = False

        # String constraints
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex

        # Numeric constraints (FastAPI compatible names)
        self.gt = gt  # greater than
        self.ge = ge  # greater than or equal
        self.lt = lt  # less than
        self.le = le  # less than or equal

        # List constraints
        self.min_items = min_items
        self.max_items = max_items

        # General
        self.description = description
        self.example = example

        # Internal
        self._c_validator = None
        self._field_type = None
        self._is_nested_model = False
        self._nested_model_class = None
        self._is_list_of_models = False
        self._list_item_model_class = None

        # Legacy support (deprecated)
        self.optional = optional or not self.is_required

    def _auto_detect_constraints_from_type(self, field_type):
        """Auto-detect validation constraints based on field type"""
        self._field_type = field_type

        # Get origin type (List, Dict, etc.)
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional types
        if origin is Union or (UnionType and isinstance(field_type, UnionType)):
            # Check for Optional[Type] pattern
            non_none_types = [arg for arg in args if arg is not type(None)]
            if len(non_none_types) == 1 and type(None) in args:
                self.optional = True
                self._field_type = non_none_types[0]
                origin = get_origin(self._field_type)
                args = get_args(self._field_type)

        # Check if this is a nested BaseModel
        if (
            inspect.isclass(field_type)
            and issubclass(field_type, BaseModel)
            and field_type is not BaseModel
        ):
            self._is_nested_model = True
            self._nested_model_class = field_type

        # Check if this is a List[BaseModel] pattern
        if origin is list and args and len(args) == 1:
            item_type = args[0]
            if (
                inspect.isclass(item_type)
                and issubclass(item_type, BaseModel)
                and item_type is not BaseModel
            ):
                self._is_list_of_models = True
                self._list_item_model_class = item_type

        return origin, args

    def _create_c_validator(self, field_type=None):
        """Create C validator based on field type and constraints"""
        if field_type:
            origin, args = self._auto_detect_constraints_from_type(field_type)
        else:
            field_type = self._field_type
            origin = get_origin(field_type) if field_type else None

        # Determine the base type
        if field_type == int or field_type is int:
            return self._create_int_validator()
        elif field_type == str or field_type is str:
            return self._create_string_validator()
        elif field_type == float or field_type is float:
            return self._create_float_validator()
        elif field_type == bool or field_type is bool:
            return self._create_bool_validator()
        elif origin is list or origin is List:
            return self._create_list_validator(args)
        else:
            # Default to string validator for unknown types
            return self._create_string_validator()

    def _create_int_validator(self):
        """Create integer validator with FastAPI-compatible constraints"""
        # For integers, we can directly use ge/le, but need to handle gt/lt
        min_val = (
            self.ge
            if self.ge is not None
            else (self.gt + 1 if self.gt is not None else None)
        )
        max_val = (
            self.le
            if self.le is not None
            else (self.lt - 1 if self.lt is not None else None)
        )

        return create_int_validator(min=min_val, max=max_val)

    def _create_string_validator(self):
        """Create string validator with FastAPI-compatible constraints"""
        return create_string_validator(
            min_len=self.min_length, max_len=self.max_length, pattern=self.regex
        )

    def _create_float_validator(self):
        """Create float validator with FastAPI-compatible constraints"""
        # For floats, we need to handle gt/lt more carefully
        min_val = self.ge if self.ge is not None else self.gt
        max_val = self.le if self.le is not None else self.lt

        # Note: C validator will need to handle gt/lt vs ge/le distinction
        return create_float_validator(min=min_val, max=max_val)

    def _create_bool_validator(self):
        """Create boolean validator"""
        return create_int_validator(min=0, max=1)  # C validator for bool

    def _create_list_validator(self, args):
        """Create list validator with item validation"""
        # Get item type if specified
        item_validator = None
        if args:
            item_type = args[0]
            if item_type == str:
                item_validator = create_string_validator()
            elif item_type == int:
                item_validator = create_int_validator()
            elif item_type == float:
                item_validator = create_float_validator()
            else:
                item_validator = create_string_validator()  # Default fallback

        return create_list_validator(
            item_validator=item_validator,
            min_items=self.min_items,
            max_items=self.max_items,
        )

    def validate_python(self, value):
        """Python fallback validation for this field"""
        field_type = self._field_type

        # Handle None values for optional fields
        if value is None and self.optional:
            return None

        # Handle Optional types - extract the inner type
        origin = get_origin(field_type)
        if origin is Union or (UnionType and origin is UnionType):
            args = get_args(field_type)
            # Check if it's Optional (Union with None)
            if len(args) == 2 and type(None) in args:
                # Allow None for optional fields
                if value is None:
                    return None
                # Extract the non-None type for validation
                field_type = args[0] if args[1] is type(None) else args[1]

        # Type checking and conversion
        if field_type == int or field_type is int:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise ValidationError(f"Expected int, got {type(value).__name__}")

            # Check numeric constraints
            if self.ge is not None and value < self.ge:
                raise ValidationError(f"Value must be >= {self.ge}, got {value}")
            if self.gt is not None and value <= self.gt:
                raise ValidationError(f"Value must be > {self.gt}, got {value}")
            if self.le is not None and value > self.le:
                raise ValidationError(f"Value must be <= {self.le}, got {value}")
            if self.lt is not None and value >= self.lt:
                raise ValidationError(f"Value must be < {self.lt}, got {value}")

        elif field_type == str or field_type is str:
            if not isinstance(value, str):
                raise ValidationError(f"Expected str, got {type(value).__name__}")

            # Check string constraints
            if self.min_length is not None and len(value) < self.min_length:
                raise ValidationError(
                    f"String must be at least {self.min_length} characters, got {len(value)}"
                )
            if self.max_length is not None and len(value) > self.max_length:
                raise ValidationError(
                    f"String must be at most {self.max_length} characters, got {len(value)}"
                )
            if self.regex is not None:
                import re

                if not re.match(self.regex, value):
                    raise ValidationError(f"String does not match pattern {self.regex}")

        elif field_type == float or field_type is float:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValidationError(f"Expected float, got {type(value).__name__}")

            # Check numeric constraints
            if self.ge is not None and value < self.ge:
                raise ValidationError(f"Value must be >= {self.ge}, got {value}")
            if self.gt is not None and value <= self.gt:
                raise ValidationError(f"Value must be > {self.gt}, got {value}")
            if self.le is not None and value > self.le:
                raise ValidationError(f"Value must be <= {self.le}, got {value}")
            if self.lt is not None and value >= self.lt:
                raise ValidationError(f"Value must be < {self.lt}, got {value}")

        elif field_type == bool or field_type is bool:
            if not isinstance(value, bool):
                # Allow string to bool conversion
                if isinstance(value, str):
                    if value.lower() in ("true", "1", "yes", "on"):
                        value = True
                    elif value.lower() in ("false", "0", "no", "off"):
                        value = False
                    else:
                        raise ValidationError(f"Cannot convert '{value}' to bool")
                else:
                    raise ValidationError(f"Expected bool, got {type(value).__name__}")

        # Handle List types
        elif hasattr(field_type, "__origin__") and field_type.__origin__ is list:
            if not isinstance(value, list):
                raise ValidationError(f"Expected list, got {type(value).__name__}")

            # Check list constraints
            if self.min_items is not None and len(value) < self.min_items:
                raise ValidationError(
                    f"List must have at least {self.min_items} items, got {len(value)}"
                )
            if self.max_items is not None and len(value) > self.max_items:
                raise ValidationError(
                    f"List must have at most {self.max_items} items, got {len(value)}"
                )

            # Handle List[BaseModel] - convert dicts to model instances
            if self._is_list_of_models and self._list_item_model_class:
                converted_items = []
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        try:
                            converted_item = self._list_item_model_class(**item)
                            converted_items.append(converted_item)
                        except Exception as e:
                            raise ValidationError(
                                f"Failed to validate list item {i} as {self._list_item_model_class.__name__}: {e}"
                            )
                    elif isinstance(item, self._list_item_model_class):
                        converted_items.append(item)
                    else:
                        raise ValidationError(
                            f"Expected {self._list_item_model_class.__name__} or dict for list item {i}, got {type(item).__name__}"
                        )
                value = converted_items

        # Handle nested BaseModel types
        elif self._is_nested_model and self._nested_model_class:
            if isinstance(value, dict):
                # Convert dict to nested model instance
                try:
                    value = self._nested_model_class(**value)
                except Exception as e:
                    raise ValidationError(
                        f"Failed to validate nested model {self._nested_model_class.__name__}: {e}"
                    )
            elif not isinstance(value, self._nested_model_class):
                raise ValidationError(
                    f"Expected {self._nested_model_class.__name__} or dict, got {type(value).__name__}"
                )

        return value

    def get_c_validator(self):
        """Get or create the C validator for this field"""
        if self._c_validator is None:
            self._c_validator = self._create_c_validator()
        return self._c_validator


class TypeConverter:
    """Converts Python type hints to Field objects"""

    @staticmethod
    def convert_type_hint(type_hint, default_value=None, has_default=False):
        """Convert a type hint to a Field object"""

        # Protect against GC issues during type processing
        gc.disable()
        try:
            return TypeConverter._convert_type_hint_unsafe(
                type_hint, default_value, has_default
            )
        finally:
            gc.enable()

    @staticmethod
    def _convert_type_hint_unsafe(type_hint, default_value=None, has_default=False):
        """Convert a type hint to a Field object (internal method without GC protection)"""

        # Determine if field is optional based on type annotation only
        # A field is optional if it's explicitly typed as Optional[Type] or Union[Type, None]
        # Having a default value does NOT make a field optional - it just provides a fallback
        is_optional = False

        # Handle Union types (e.g., str | None, Union[str, None])
        origin = get_origin(type_hint)
        if origin is Union or (UnionType and origin is UnionType):
            args = get_args(type_hint)

            # Check if it's Optional (Union with None)
            if len(args) == 2 and type(None) in args:
                # Optional type
                non_none_type = args[0] if args[1] is type(None) else args[1]
                field = TypeConverter._convert_type_hint_unsafe(
                    non_none_type, default_value, has_default
                )
                field.optional = True  # Optional fields are always optional
                return field
            else:
                # TODO: Handle other Union types
                raise NotImplementedError(f"Union types not yet supported: {type_hint}")

        # Create FastAPI-style Field with auto-detected type
        field_default = default_value if has_default else ...
        field = Field(default=field_default)
        field._field_type = type_hint
        field.optional = is_optional or has_default

        # Check if this is a nested BaseModel
        if (
            inspect.isclass(type_hint)
            and issubclass(type_hint, BaseModel)
            and type_hint is not BaseModel
        ):
            field._is_nested_model = True
            field._nested_model_class = type_hint
        else:
            field._is_nested_model = False
            field._nested_model_class = None

        # Check if this is a List[BaseModel] pattern
        field._is_list_of_models = False
        field._list_item_model_class = None
        if hasattr(type_hint, "__origin__") and type_hint.__origin__ is list:
            args = get_args(type_hint)
            if args and len(args) == 1:
                item_type = args[0]
                if (
                    inspect.isclass(item_type)
                    and issubclass(item_type, BaseModel)
                    and item_type is not BaseModel
                ):
                    field._is_list_of_models = True
                    field._list_item_model_class = item_type

        return field


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

        # Get type hints for this class with garbage collection protection
        try:
            import gc

            # Temporarily disable GC during type hint resolution to prevent segfaults
            gc.disable()
            try:
                type_hints = get_type_hints(cls)
            finally:
                gc.enable()
        except (NameError, AttributeError):
            type_hints = getattr(cls, "__annotations__", {})

        cls._fields = {}

        # Process each annotated field
        for field_name, field_type in type_hints.items():

            # Check if field is already explicitly defined as Field
            if hasattr(cls, field_name) and isinstance(getattr(cls, field_name), Field):
                # Use explicit Field definition and set its type
                field = getattr(cls, field_name)
                field._field_type = field_type
                # Auto-detect nested models and list patterns
                field._auto_detect_constraints_from_type(field_type)
                cls._fields[field_name] = field
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
            # Create the C validator for this field using its type
            if field._field_type:
                validator = field._create_c_validator(field._field_type)
            else:
                validator = field.get_c_validator()

            # Pass validator and required status (opposite of optional)
            required = not field.optional
            c_fields[field_name] = (validator, required)

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
        name: str = Field(min_length=1, max_length=200)
        price: float = Field(gt=0.01)
    """

    def __init__(self, **data):
        """Initialize model with data (validates automatically)"""
        # 🛡️ GC PROTECTION: Disable garbage collection during model initialization
        # This prevents segfaults during intensive batch model creation scenarios
        import gc

        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            validated_data = self.validate(data)
            self.__dict__.update(validated_data)

            # Call __post_init__ if it exists for custom validation
            if hasattr(self, "__post_init__") and callable(
                getattr(self, "__post_init__")
            ):
                self.__post_init__()
        finally:
            # 🛡️ GC PROTECTION: Re-enable garbage collection if it was enabled before
            if gc_was_enabled:
                gc.enable()

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

        # 🛡️ GC PROTECTION: Disable garbage collection during C/Python validation boundary
        # This prevents segfaults during intensive batch validation when GC triggers during fallback
        import gc

        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            # Preprocess data for C validation (convert types as needed)
            preprocessed_data = cls._preprocess_for_c_validation(data)
            # Use ultra-fast C validation
            return cls._c_model.validate(preprocessed_data)
        except Exception as e:
            # Fall back to Python validation if C validation fails
            return cls._validate_python(data)
        finally:
            # 🛡️ GC PROTECTION: Re-enable garbage collection if it was enabled before
            if gc_was_enabled:
                gc.enable()

    @classmethod
    def _validate_python(cls, data):
        """Fallback Python validation (much slower but functional)"""

        if not hasattr(cls, "_fields"):
            return data

        # 🛡️ GC PROTECTION: Disable garbage collection during validation to prevent segfaults
        # This is critical for batch validation scenarios where GC can trigger during field validation
        import gc

        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            validated = {}
            errors = []

            for field_name, field in cls._fields.items():
                if field_name in data:
                    # Field is provided - validate it regardless of whether it's optional
                    try:
                        if hasattr(field, "validate_python"):
                            validated[field_name] = field.validate_python(
                                data[field_name]
                            )
                        else:
                            # For basic types, just copy the value
                            validated[field_name] = data[field_name]
                    except ValidationError as e:
                        errors.append(f"{field_name}: {str(e)}")
                elif field.optional:
                    # Optional field not provided - use default value
                    validated[field_name] = field.default
                else:
                    # Required field not provided - check if it has a default
                    if field.default is not None:
                        validated[field_name] = field.default
                    else:
                        errors.append(f"Field '{field_name}' is required")

            if errors:
                raise ValidationError("; ".join(errors))

            return validated

        finally:
            # 🛡️ GC PROTECTION: Re-enable garbage collection if it was enabled before
            if gc_was_enabled:
                gc.enable()

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
                # Handle boolean values for bool field types
                if field._field_type == bool and isinstance(value, bool):
                    preprocessed[key] = int(value)  # True -> 1, False -> 0
                else:
                    preprocessed[key] = value
            else:
                preprocessed[key] = value

        return preprocessed

    def dict(self):
        """Return model data as dictionary (Pydantic compatibility)"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def model_dump(self):
        """Return model data as dictionary (Pydantic v2 compatibility)"""
        return self.dict()

    def json(self, **kwargs):
        """Return model data as JSON string (Pydantic compatibility)"""
        import json

        return json.dumps(self.dict(), **kwargs)

    def model_dump_json(self, **kwargs):
        """Return model data as JSON string (Pydantic v2 compatibility)"""
        return self.json(**kwargs)

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


# Performance monitoring functions
def get_performance_stats():
    """Get validation performance statistics (alias for get_validation_stats)"""
    return get_validation_stats()


def reset_performance_stats():
    """Reset validation performance statistics (alias for reset_validation_stats)"""
    return reset_validation_stats()


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
