from catzilla import Catzilla
from catzilla.validation import BaseModel

app = Catzilla()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/")
def read_root(request):
    return {"message": "Hello from Catzilla! 🚀"}

@app.post("/users/")
def create_user(request, user: User):
    return {"user": user.name, "status": "created"}

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
