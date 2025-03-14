import enum
from datetime import datetime
from sqlalchemy import (
    DateTime, func, Integer, String, Text, ForeignKey, Table, Column, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# Промежуточная таблица для связи "многие ко многим" между пользователями и болезнями
user_diseases = Table(
    "user_diseases",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("disease_id", Integer, ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True)
)

# Промежуточная таблица для связи "многие ко многим" между болезнями и симптомами
disease_symptoms = Table(
    "disease_symptoms",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True),
    Column("symptom_id", Integer, ForeignKey("symptoms.id", ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, unique=True, index=True, nullable=False)

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    diseases = relationship("Disease", secondary=user_diseases, back_populates="users")
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship("User", secondary=user_diseases, back_populates="diseases")
    symptoms = relationship("Symptom", secondary=disease_symptoms, back_populates="diseases")


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    diseases = relationship("Disease", secondary=disease_symptoms, back_populates="symptoms")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")


# **Pydantic-модели**

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class UserResponse(BaseModel):
    id: int
    nickname: str
    email: EmailStr

    class Config:
        from_attributes = True


class DiseaseCreate(BaseModel):
    name: str
    description: str


class SymptomCreate(BaseModel):
    name: str


class SymptomResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DiseaseSymptomLink(BaseModel):
    disease_id: int
    symptom_id: int


# **ВОССТАНОВЛЕННЫЕ МОДЕЛИ**
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AllUsersProfilesMain(BaseModel):
    id: int
    email: EmailStr
    nickname: str

    class Config:
        from_attributes = True



from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)  # Название показателя (например, "Давление")
    value = Column(String, nullable=False)  # Значение показателя (например, "120/80")
    created = Column(DateTime, default=func.now())  # Явно указываем поле created
    user = relationship("User", back_populates="health_metrics")


class HealthMetricCreate(BaseModel):
    name: str
    value: str

from datetime import datetime

class HealthMetricResponse(BaseModel):
    id: int
    name: str
    value: str
    created: datetime  # Добавляем поле created

    class Config:
        from_attributes = True  # Ранее known as `orm_mode = True`

