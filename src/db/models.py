import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    DateTime, func, Integer, String, Text, ForeignKey, Table, Column, CheckConstraint, Float
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
    Column("symptom_id", Integer, ForeignKey("symptoms.id", ondelete="CASCADE"), primary_key=True),
    Column("weight", Float, default=1.0, nullable=False)  # Вес симптома, по умолчанию 1.0
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)  # Возраст, может быть необязательным

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    diseases = relationship("Disease", secondary=user_diseases, back_populates="users")
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Оставляем только диапазон возраста
    age_min = Column(Integer, nullable=True)  # Минимальный возраст для "предпочитаемого" диапазона
    age_max = Column(Integer, nullable=True)  # Максимальный возраст для "предпочитаемого" диапазона

    users = relationship("User", secondary=user_diseases, back_populates="diseases")
    symptoms = relationship("Symptom", secondary=disease_symptoms, back_populates="symptoms")


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
    age: Optional[int] = None  # Возраст необязательный


class UserResponse(BaseModel):
    id: int
    nickname: str
    email: EmailStr
    age: Optional[int] = None

    class Config:
        from_attributes = True


class DiseaseCreate(BaseModel):
    name: str
    description: str
    age_min: Optional[int] = None  # Минимальный возраст (необязательное)
    age_max: Optional[int] = None  # Максимальный возраст (необязательное)


class DiseaseResponse(BaseModel):
    id: int
    name: str
    description: str
    age_min: Optional[int]
    age_max: Optional[int]

    class Config:
        from_attributes = True


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
    weight: float = 1.0  # Добавляем вес для связи


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


# Модели для предсказания болезни
class PredictionRequest(BaseModel):
    symptom_names: List[str]
    # Возраст уже есть у пользователя, не нужно передавать его отдельно


class PredictionItem(BaseModel):
    disease: str
    description: str
    probability: float


class PredictionResponse(BaseModel):
    predictions: List[PredictionItem]


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


class HealthMetricResponse(BaseModel):
    id: int
    name: str
    value: str
    created: datetime  # Добавляем поле created

    class Config:
        from_attributes = True