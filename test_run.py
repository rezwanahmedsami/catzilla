from catzilla import Catzilla, JSONResponse, BaseModel, Field, ValidationError
from typing import Optional

app = Catzilla()

class UserWithCustomValidation(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(ge=13, le=120)
    bio: Optional[str] = Field(None, max_length=500)

    def __post_init__(self):
        """Custom validation after field validation"""
        print("Running custom validation logic...")
        # Custom business rules
        if self.age < 18 and self.bio and len(self.bio) > 100:
            raise ValidationError(
                "Users under 18 cannot have bio longer than 100 characters"
            )

        if "admin" in self.email and self.age < 21:
            raise ValidationError(
                "Admin users must be at least 21 years old"
            )

@app.post("/validated-users")
def create_validated_user(request, user: UserWithCustomValidation):
    return JSONResponse({
        "message": "User created with custom validation",
        "user": {
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "bio": user.bio
        },
        "custom_rules_applied": True
    }, status_code=201)

if __name__ == "__main__":
    app.listen(port=8000)
