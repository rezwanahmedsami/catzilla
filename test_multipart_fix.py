#!/usr/bin/env python3
"""Test multipart form data validation with fixed C-level parsing"""

from pydantic import BaseModel, Field
from catzilla import Catzilla, Request, Response
from catzilla.validation import auto_validation

app = Catzilla()

# Define the form model with validation
class UserFormData(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's name")
    age: int = Field(..., ge=18, le=120, description="User's age")
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Valid email address")

@app.post("/form-validation")
@auto_validation
def test_form_validation(request: Request, form_data: UserFormData) -> Response:
    """Test endpoint for multipart form validation"""
    print(f"✅ Form validation successful!")
    print(f"   Name: {form_data.name}")
    print(f"   Age: {form_data.age}")
    print(f"   Email: {form_data.email}")

    return Response(
        content=f"Form validated successfully! Name: {form_data.name}, Age: {form_data.age}, Email: {form_data.email}",
        content_type="text/plain"
    )

if __name__ == "__main__":
    print("🚀 Starting Catzilla form validation test server...")
    print("📝 Test with:")
    print("   curl -X POST -F 'name=John Doe' -F 'age=25' -F 'email=john@example.com' http://localhost:8000/form-validation")
    print("   curl -X POST -F 'name=X' -F 'age=17' -F 'email=invalid' http://localhost:8000/form-validation")

    app.run(host="0.0.0.0", port=8000)
