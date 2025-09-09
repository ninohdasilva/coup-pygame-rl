from pydantic import BaseModel
from character import Character

class Card(BaseModel):
    character: Character
    is_revealed: bool