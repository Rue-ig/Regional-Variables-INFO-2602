from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from pydantic import EmailStr

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    reviews: list["Review"] = Relationship(back_populates="user")
    photos: list["Photo"] = Relationship(back_populates="user")