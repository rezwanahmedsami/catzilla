"""
Comprehensive tests for Catzilla's FastAPI-style Field() validation system.

Tests cover the new unified Field() system including:
1. FastAPI-compatible Field() constraints (ge, gt, le, lt, min_length, max_length, regex)
2. Nested BaseModel validation with automatic dict conversion
3. List validation with min_items, max_items
4. Optional field handling
5. Performance benchmarks
6. Error handling and validation messages
"""

import pytest
import time
import gc
from typing import Optional, List, Dict, Union

# Import Catzilla validation components
try:
    from catzilla.validation import (
        BaseModel,
        Field,
        ValidationError,
    )
except ImportError:
    pytest.skip("Catzilla validation module not available", allow_module_level=True)


@pytest.fixture(autouse=True)
def force_python_validation():
    """
    Force Python validation for consistent test results.
    The C validation may have different behavior, so we test the Python implementation.
    """
    original_c_models = {}

    def patch_class(cls):
        if hasattr(cls, '_c_model'):
            original_c_models[cls] = cls._c_model
            cls._c_model = None

    # Patch any test classes that get created
    original_new = BaseModel.__class__.__new__

    def patched_new(mcs, name, bases, namespace, **kwargs):
        cls = original_new(mcs, name, bases, namespace, **kwargs)
        if hasattr(cls, '_c_model'):
            original_c_models[cls] = cls._c_model
            cls._c_model = None
        return cls

    BaseModel.__class__.__new__ = patched_new

    yield

    # Restore original state
    BaseModel.__class__.__new__ = original_new
    for cls, c_model in original_c_models.items():
        cls._c_model = c_model


class TestFastAPIFieldBasics:
    """Test basic FastAPI-style Field() functionality."""

    def test_field_with_default_value(self):
        """Test Field with default values."""

        class UserModel(BaseModel):
            name: str = Field(default="Unknown", min_length=1, max_length=50)
            age: int = Field(default=18, ge=0, le=120)
            active: bool = Field(default=True)

        # Test with explicit values
        user1 = UserModel(name="John", age=25, active=False)
        assert user1.name == "John"
        assert user1.age == 25
        assert user1.active == False

        # Test with defaults
        user2 = UserModel()
        assert user2.name == "Unknown"
        assert user2.age == 18
        assert user2.active == True

        # Test partial defaults
        user3 = UserModel(name="Jane")
        assert user3.name == "Jane"
        assert user3.age == 18
        assert user3.active == True

    def test_field_without_default_required(self):
        """Test that Field without default is required."""

        class ProductModel(BaseModel):
            name: str = Field(min_length=1, max_length=100)
            price: float = Field(gt=0.0)

        # Valid case
        product = ProductModel(name="Widget", price=9.99)
        assert product.name == "Widget"
        assert product.price == 9.99

        # Missing required field
        with pytest.raises(ValidationError):
            ProductModel(name="Widget")  # Missing price

        with pytest.raises(ValidationError):
            ProductModel(price=9.99)  # Missing name

    def test_field_description_metadata(self):
        """Test Field description and metadata."""

        class DocumentedModel(BaseModel):
            id: int = Field(ge=1, description="Unique identifier")
            title: str = Field(min_length=1, max_length=200, description="Document title")
            content: Optional[str] = Field(None, description="Document content")

        # Test that model works regardless of description
        doc = DocumentedModel(id=1, title="Test Document", content="Some content")
        assert doc.id == 1
        assert doc.title == "Test Document"
        assert doc.content == "Some content"

        # Test without optional field
        doc2 = DocumentedModel(id=2, title="Another Document")
        assert doc2.id == 2
        assert doc2.title == "Another Document"
        assert doc2.content is None


class TestNumericConstraints:
    """Test numeric constraints: ge, gt, le, lt."""

    def test_integer_constraints(self):
        """Test integer field constraints."""

        class ScoreModel(BaseModel):
            score: int = Field(ge=0, le=100)
            level: int = Field(gt=0, lt=10)
            bonus: int = Field(ge=0)

        # Valid cases
        valid_score = ScoreModel(score=85, level=5, bonus=10)
        assert valid_score.score == 85
        assert valid_score.level == 5
        assert valid_score.bonus == 10

        # Test boundary values
        boundary_score = ScoreModel(score=0, level=1, bonus=0)  # ge=0, gt=0, ge=0
        assert boundary_score.score == 0
        assert boundary_score.level == 1
        assert boundary_score.bonus == 0

        boundary_score2 = ScoreModel(score=100, level=9, bonus=1000)  # le=100, lt=10
        assert boundary_score2.score == 100
        assert boundary_score2.level == 9
        assert boundary_score2.bonus == 1000

        # Invalid cases
        with pytest.raises(ValidationError) as exc_info:
            ScoreModel(score=-1, level=5, bonus=10)  # score < 0 (violates ge=0)
        assert "must be >= 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ScoreModel(score=101, level=5, bonus=10)  # score > 100 (violates le=100)
        assert "must be <= 100" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ScoreModel(score=50, level=0, bonus=10)  # level <= 0 (violates gt=0)
        assert "must be > 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ScoreModel(score=50, level=10, bonus=10)  # level >= 10 (violates lt=10)
        assert "must be < 10" in str(exc_info.value)

    def test_float_constraints(self):
        """Test float field constraints."""

        class MeasurementModel(BaseModel):
            temperature: float = Field(ge=-273.15, le=1000.0)
            pressure: float = Field(gt=0.0)
            humidity: float = Field(ge=0.0, le=100.0)

        # Valid cases
        measurement = MeasurementModel(temperature=25.5, pressure=101.3, humidity=65.8)
        assert measurement.temperature == 25.5
        assert measurement.pressure == 101.3
        assert measurement.humidity == 65.8

        # Test boundary values
        extreme = MeasurementModel(temperature=-273.15, pressure=0.001, humidity=0.0)
        assert extreme.temperature == -273.15
        assert extreme.pressure == 0.001
        assert extreme.humidity == 0.0

        # Invalid cases
        with pytest.raises(ValidationError) as exc_info:
            MeasurementModel(temperature=-300.0, pressure=101.3, humidity=50.0)
        assert "must be >= -273.15" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MeasurementModel(temperature=25.0, pressure=0.0, humidity=50.0)
        assert "must be > 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MeasurementModel(temperature=25.0, pressure=101.3, humidity=150.0)
        assert "must be <= 100" in str(exc_info.value)


class TestStringConstraints:
    """Test string constraints: min_length, max_length, regex."""

    def test_length_constraints(self):
        """Test string length constraints."""

        class TextModel(BaseModel):
            username: str = Field(min_length=3, max_length=20)
            title: str = Field(max_length=100)
            code: str = Field(min_length=5)

        # Valid cases
        text = TextModel(username="john_doe", title="A Great Title", code="ABC123")
        assert text.username == "john_doe"
        assert text.title == "A Great Title"
        assert text.code == "ABC123"

        # Boundary cases
        boundary = TextModel(username="abc", title="", code="12345")  # min lengths
        assert boundary.username == "abc"
        assert boundary.title == ""
        assert boundary.code == "12345"

        long_title = "x" * 100
        boundary2 = TextModel(username="abcdefghij12345", title=long_title, code="ABCDEF")
        assert boundary2.title == long_title

        # Invalid cases
        with pytest.raises(ValidationError) as exc_info:
            TextModel(username="ab", title="Good", code="12345")  # username too short
        assert "must be at least 3 characters" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            TextModel(username="this_username_is_way_too_long", title="Good", code="12345")
        assert "must be at most 20 characters" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            TextModel(username="good", title="Good", code="1234")  # code too short
        assert "must be at least 5 characters" in str(exc_info.value)

        long_title = "x" * 101  # 101 characters
        with pytest.raises(ValidationError) as exc_info:
            TextModel(username="good", title=long_title, code="12345")
        assert "must be at most 100 characters" in str(exc_info.value)

    def test_regex_constraints(self):
        """Test regex pattern constraints."""

        class PatternModel(BaseModel):
            email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
            phone: str = Field(regex=r'^\+?1?-?[0-9]{3}-?[0-9]{3}-?[0-9]{4}$')
            username: str = Field(regex=r'^[a-zA-Z0-9_]+$')

        # Valid cases
        pattern = PatternModel(
            email="user@example.com",
            phone="123-456-7890",
            username="john_doe123"
        )
        assert pattern.email == "user@example.com"
        assert pattern.phone == "123-456-7890"
        assert pattern.username == "john_doe123"

        # More valid patterns
        pattern2 = PatternModel(
            email="test.email+tag@domain.co.uk",
            phone="+1-555-123-4567",
            username="user_123"
        )
        assert pattern2.email == "test.email+tag@domain.co.uk"
        assert pattern2.phone == "+1-555-123-4567"
        assert pattern2.username == "user_123"

        # Invalid cases
        with pytest.raises(ValidationError) as exc_info:
            PatternModel(email="invalid-email", phone="123-456-7890", username="john_doe")
        assert "does not match pattern" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            PatternModel(email="user@example.com", phone="invalid-phone", username="john_doe")
        assert "does not match pattern" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            PatternModel(email="user@example.com", phone="123-456-7890", username="john-doe!")
        assert "does not match pattern" in str(exc_info.value)

    def test_combined_string_constraints(self):
        """Test combining multiple string constraints."""

        class CombinedModel(BaseModel):
            secure_code: str = Field(
                min_length=8,
                max_length=16,
                regex=r'^[A-Z0-9_]+$'
            )

        # Valid cases
        combined = CombinedModel(secure_code="ABC123_XYZ")
        assert combined.secure_code == "ABC123_XYZ"

        combined2 = CombinedModel(secure_code="12345678")  # Min length boundary
        assert combined2.secure_code == "12345678"

        combined3 = CombinedModel(secure_code="ABCD1234EFGH5678")  # Max length boundary
        assert combined3.secure_code == "ABCD1234EFGH5678"

        # Invalid cases - too short
        with pytest.raises(ValidationError) as exc_info:
            CombinedModel(secure_code="ABC123")
        assert "must be at least 8 characters" in str(exc_info.value)

        # Invalid cases - too long
        with pytest.raises(ValidationError) as exc_info:
            CombinedModel(secure_code="ABC123_XYZ_TOOLONG")
        assert "must be at most 16 characters" in str(exc_info.value)

        # Invalid cases - wrong pattern
        with pytest.raises(ValidationError) as exc_info:
            CombinedModel(secure_code="abc123_xyz")  # lowercase not allowed
        assert "does not match pattern" in str(exc_info.value)


class TestListConstraints:
    """Test list constraints: min_items, max_items."""

    def test_list_item_constraints(self):
        """Test list min_items and max_items constraints."""

        class ListModel(BaseModel):
            tags: List[str] = Field(min_items=1, max_items=5)
            scores: List[float] = Field(max_items=10)
            required_list: List[int] = Field(min_items=2)

        # Valid cases
        list_model = ListModel(
            tags=["python", "web", "api"],
            scores=[95.5, 87.2, 92.1],
            required_list=[1, 2, 3]
        )
        assert list_model.tags == ["python", "web", "api"]
        assert list_model.scores == [95.5, 87.2, 92.1]
        assert list_model.required_list == [1, 2, 3]

        # Boundary cases
        boundary = ListModel(
            tags=["single"],  # min_items=1
            scores=[],  # max_items=10, no min
            required_list=[1, 2]  # min_items=2
        )
        assert boundary.tags == ["single"]
        assert boundary.scores == []
        assert boundary.required_list == [1, 2]

        max_tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]  # max_items=5
        boundary2 = ListModel(
            tags=max_tags,
            scores=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],  # max_items=10
            required_list=[1, 2, 3, 4, 5]
        )
        assert boundary2.tags == max_tags
        assert len(boundary2.scores) == 10

        # Invalid cases
        with pytest.raises(ValidationError) as exc_info:
            ListModel(
                tags=[],  # Empty list, violates min_items=1
                scores=[1.0],
                required_list=[1, 2]
            )
        assert "must have at least 1 items" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ListModel(
                tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],  # 6 items, violates max_items=5
                scores=[1.0],
                required_list=[1, 2]
            )
        assert "must have at most 5 items" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ListModel(
                tags=["tag1"],
                scores=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],  # 11 items, violates max_items=10
                required_list=[1, 2]
            )
        assert "must have at most 10 items" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ListModel(
                tags=["tag1"],
                scores=[1.0],
                required_list=[1]  # Only 1 item, violates min_items=2
            )
        assert "must have at least 2 items" in str(exc_info.value)


class TestNestedModels:
    """Test nested BaseModel validation with automatic dict conversion."""

    def test_simple_nested_model(self):
        """Test basic nested model functionality."""

        class Address(BaseModel):
            street: str = Field(min_length=5, max_length=100)
            city: str = Field(min_length=2, max_length=50)
            zip_code: str = Field(regex=r'^\d{5}(-\d{4})?$')

        class Person(BaseModel):
            name: str = Field(min_length=1, max_length=100)
            age: int = Field(ge=0, le=150)
            address: Address

        # Test with nested dict (automatic conversion)
        person_data = {
            "name": "John Doe",
            "age": 30,
            "address": {
                "street": "123 Main Street",
                "city": "Anytown",
                "zip_code": "12345"
            }
        }

        person = Person(**person_data)
        assert person.name == "John Doe"
        assert person.age == 30
        assert isinstance(person.address, Address)
        assert person.address.street == "123 Main Street"
        assert person.address.city == "Anytown"
        assert person.address.zip_code == "12345"

        # Test with pre-created nested model
        address = Address(street="456 Oak Avenue", city="Other City", zip_code="54321")
        person2 = Person(name="Jane Smith", age=25, address=address)
        assert person2.name == "Jane Smith"
        assert person2.age == 25
        assert person2.address.street == "456 Oak Avenue"
        assert person2.address.city == "Other City"
        assert person2.address.zip_code == "54321"

    def test_nested_model_validation_errors(self):
        """Test that nested model validation errors are properly reported."""

        class Address(BaseModel):
            street: str = Field(min_length=5)
            city: str = Field(min_length=2)
            zip_code: str = Field(regex=r'^\d{5}(-\d{4})?$')

        class Person(BaseModel):
            name: str = Field(min_length=1)
            address: Address

        # Test nested validation error
        with pytest.raises(ValidationError) as exc_info:
            Person(
                name="John",
                address={
                    "street": "123",  # Too short
                    "city": "SF",
                    "zip_code": "invalid"  # Invalid format
                }
            )
        error_msg = str(exc_info.value)
        assert "nested model" in error_msg.lower()
        assert "Address" in error_msg

        # Test missing nested fields
        with pytest.raises(ValidationError) as exc_info:
            Person(
                name="John",
                address={
                    "street": "123 Main Street"
                    # Missing city and zip_code
                }
            )
        error_msg = str(exc_info.value)
        assert "nested model" in error_msg.lower()
        assert "Address" in error_msg

    def test_multiple_nested_models(self):
        """Test models with multiple nested models."""

        class ContactInfo(BaseModel):
            email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
            phone: str = Field(min_length=10, max_length=15)

        class Address(BaseModel):
            street: str = Field(min_length=5)
            city: str = Field(min_length=2)

        class Company(BaseModel):
            name: str = Field(min_length=2, max_length=100)
            address: Address
            contact: ContactInfo
            employee_count: int = Field(ge=1)

        # Test with all nested dicts
        company_data = {
            "name": "Tech Corp",
            "address": {
                "street": "123 Business Ave",
                "city": "Tech City"
            },
            "contact": {
                "email": "info@techcorp.com",
                "phone": "555-123-4567"
            },
            "employee_count": 100
        }

        company = Company(**company_data)
        assert company.name == "Tech Corp"
        assert isinstance(company.address, Address)
        assert isinstance(company.contact, ContactInfo)
        assert company.address.street == "123 Business Ave"
        assert company.contact.email == "info@techcorp.com"
        assert company.employee_count == 100


class TestOptionalFields:
    """Test Optional field handling with Field constraints."""

    def test_optional_fields_with_constraints(self):
        """Test Optional fields with Field constraints."""

        class OptionalModel(BaseModel):
            required_name: str = Field(min_length=1, max_length=50)
            optional_age: Optional[int] = Field(None, ge=0, le=150)
            optional_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
            optional_tags: Optional[List[str]] = Field(None, min_items=1, max_items=5)

        # Test with all fields provided and valid
        full_model = OptionalModel(
            required_name="John Doe",
            optional_age=30,
            optional_email="john@example.com",
            optional_tags=["python", "web"]
        )
        assert full_model.required_name == "John Doe"
        assert full_model.optional_age == 30
        assert full_model.optional_email == "john@example.com"
        assert full_model.optional_tags == ["python", "web"]

        # Test with only required field
        minimal_model = OptionalModel(required_name="Jane Smith")
        assert minimal_model.required_name == "Jane Smith"
        assert minimal_model.optional_age is None
        assert minimal_model.optional_email is None
        assert minimal_model.optional_tags is None

        # Test with some optional fields
        partial_model = OptionalModel(
            required_name="Bob Wilson",
            optional_age=25,
            optional_tags=["coding"]
        )
        assert partial_model.required_name == "Bob Wilson"
        assert partial_model.optional_age == 25
        assert partial_model.optional_email is None
        assert partial_model.optional_tags == ["coding"]

        # Test validation of optional fields when provided
        with pytest.raises(ValidationError) as exc_info:
            OptionalModel(
                required_name="Test",
                optional_age=-5  # Invalid: negative age
            )
        assert "must be >= 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            OptionalModel(
                required_name="Test",
                optional_email="invalid-email"  # Invalid: bad email format
            )
        assert "does not match pattern" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            OptionalModel(
                required_name="Test",
                optional_tags=[]  # Invalid: empty list violates min_items=1
            )
        assert "must have at least 1 items" in str(exc_info.value)


class TestComplexScenarios:
    """Test complex validation scenarios combining multiple features."""

    def test_complex_nested_with_lists_and_constraints(self):
        """Test complex model with nested models, lists, and various constraints."""

        class Tag(BaseModel):
            name: str = Field(min_length=1, max_length=30)
            category: str = Field(regex=r'^[a-z]+$')

        class Author(BaseModel):
            name: str = Field(min_length=2, max_length=100)
            email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
            bio: Optional[str] = Field(None, max_length=500)

        class Article(BaseModel):
            title: str = Field(min_length=5, max_length=200)
            content: str = Field(min_length=10)
            author: Author
            tags: List[Tag] = Field(min_items=1, max_items=10)
            published: bool = Field(default=False)
            rating: Optional[float] = Field(None, ge=0.0, le=5.0)

        # Create complex test data
        article_data = {
            "title": "Advanced Python Validation",
            "content": "This is a comprehensive article about Python validation techniques...",
            "author": {
                "name": "Jane Developer",
                "email": "jane@dev.com",
                "bio": "Experienced Python developer"
            },
            "tags": [
                {"name": "python", "category": "language"},
                {"name": "validation", "category": "technique"},
                {"name": "fastapi", "category": "framework"}
            ],
            "published": True,
            "rating": 4.5
        }

        article = Article(**article_data)
        assert article.title == "Advanced Python Validation"
        assert isinstance(article.author, Author)
        assert article.author.name == "Jane Developer"
        assert len(article.tags) == 3
        assert all(isinstance(tag, Tag) for tag in article.tags)
        assert article.tags[0].name == "python"
        assert article.tags[0].category == "language"
        assert article.published == True
        assert article.rating == 4.5

        # Test with minimal data (optional fields)
        minimal_data = {
            "title": "Short Article",
            "content": "Brief content here",
            "author": {
                "name": "Bob Writer",
                "email": "bob@write.com"
            },
            "tags": [
                {"name": "test", "category": "demo"}
            ]
        }

        minimal_article = Article(**minimal_data)
        assert minimal_article.title == "Short Article"
        assert minimal_article.author.bio is None
        assert minimal_article.published == False  # Default
        assert minimal_article.rating is None
        assert len(minimal_article.tags) == 1

    def test_performance_with_field_constraints(self):
        """Test performance of Field validation system."""

        class PerformanceModel(BaseModel):
            id: int = Field(ge=1, le=1000000)
            name: str = Field(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
            score: float = Field(ge=0.0, le=100.0)
            tags: List[str] = Field(min_items=1, max_items=5)
            active: bool = Field(default=True)

        # Benchmark validation performance
        test_data = {
            "id": 12345,
            "name": "performance_test_user",
            "score": 85.5,
            "tags": ["python", "validation", "performance"]
        }

        iterations = 1000
        start_time = time.perf_counter()

        for i in range(iterations):
            # Vary the data slightly for realistic testing
            data = test_data.copy()
            data["id"] = i + 1
            data["name"] = f"user_{i}"
            data["score"] = float((i % 100) + 0.5)

            model = PerformanceModel(**data)
            assert model.id == i + 1
            assert model.name == f"user_{i}"

        end_time = time.perf_counter()
        duration = end_time - start_time
        validations_per_sec = iterations / duration

        print(f"Field validation performance: {validations_per_sec:.0f} validations/sec")
        print(f"Average time per validation: {(duration * 1000000) / iterations:.2f} microseconds")

        # Should be reasonably fast (we're testing Python fallback)
        assert validations_per_sec > 500, f"Performance too slow: {validations_per_sec:.0f}/sec"

    def test_error_accumulation(self):
        """Test that multiple validation errors are properly accumulated."""

        class MultiErrorModel(BaseModel):
            short_string: str = Field(min_length=10)
            large_number: int = Field(le=100)
            invalid_email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
            empty_list: List[str] = Field(min_items=1)

        # Test multiple validation errors at once
        with pytest.raises(ValidationError) as exc_info:
            MultiErrorModel(
                short_string="short",      # Too short
                large_number=200,          # Too large
                invalid_email="not-email", # Invalid format
                empty_list=[]              # Empty list
            )

        error_msg = str(exc_info.value)
        # Should contain information about multiple errors
        # The exact format may vary, but should include field names
        assert "short_string" in error_msg or "must be at least" in error_msg
        assert "large_number" in error_msg or "must be <=" in error_msg
        assert "invalid_email" in error_msg or "does not match pattern" in error_msg
        assert "empty_list" in error_msg or "must have at least" in error_msg


class TestFieldSystemStability:
    """Test Field system stability and edge cases."""

    def test_memory_safety_with_fields(self):
        """Test memory safety with Field constraints."""

        class StabilityModel(BaseModel):
            name: str = Field(min_length=1, max_length=100)
            value: int = Field(ge=0, le=1000)
            optional_data: Optional[str] = Field(None, max_length=200)

        # Create many models to test memory stability
        models = []
        for i in range(200):  # Moderate number to avoid memory issues
            model = StabilityModel(
                name=f"test_{i}",
                value=i % 1000,
                optional_data=f"data_{i}" if i % 2 == 0 else None
            )
            models.append(model)

        # Verify all models are correct
        for i, model in enumerate(models):
            assert model.name == f"test_{i}"
            assert model.value == i % 1000
            if i % 2 == 0:
                assert model.optional_data == f"data_{i}"
            else:
                assert model.optional_data is None

        # Clean up
        models.clear()
        gc.collect()

    def test_field_type_consistency(self):
        """Test that Field types are consistent and properly detected."""

        class TypeTestModel(BaseModel):
            int_field: int = Field(ge=0)
            str_field: str = Field(min_length=1)
            float_field: float = Field(gt=0.0)
            bool_field: bool = Field(default=True)
            list_field: List[str] = Field(min_items=0, max_items=5)
            optional_field: Optional[int] = Field(None, ge=0)

        # Test that fields have correct type detection
        assert "int_field" in TypeTestModel._fields
        assert "str_field" in TypeTestModel._fields
        assert "float_field" in TypeTestModel._fields
        assert "bool_field" in TypeTestModel._fields
        assert "list_field" in TypeTestModel._fields
        assert "optional_field" in TypeTestModel._fields

        # Test with valid data of all types
        model = TypeTestModel(
            int_field=42,
            str_field="test",
            float_field=3.14,
            bool_field=False,
            list_field=["a", "b"],
            optional_field=100
        )

        assert model.int_field == 42
        assert model.str_field == "test"
        assert model.float_field == 3.14
        assert model.bool_field == False
        assert model.list_field == ["a", "b"]
        assert model.optional_field == 100

    def test_edge_case_values(self):
        """Test edge case values that might cause issues."""

        class EdgeCaseModel(BaseModel):
            zero_int: int = Field(ge=0)
            empty_string: str = Field(min_length=0)  # Allow empty
            small_float: float = Field(gt=0.0)
            large_list: List[str] = Field(max_items=1000)

        # Test edge cases
        edge_model = EdgeCaseModel(
            zero_int=0,
            empty_string="",
            small_float=0.000001,
            large_list=["item"] * 500  # Large but under limit
        )

        assert edge_model.zero_int == 0
        assert edge_model.empty_string == ""
        assert edge_model.small_float == 0.000001
        assert len(edge_model.large_list) == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
