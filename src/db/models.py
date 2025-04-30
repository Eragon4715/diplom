import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, func, Integer, String, Text, ForeignKey, Table, Column, CheckConstraint, Float
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# Промежуточная таблица для связии "многие ко многим" между пользователями и болезнями
class UserDisease(Base):
    __tablename__ = "user_diseases"

    id = Column(Integer, primary_key=True, index=True)  # Добавляем отдельный первичный ключ
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False)
    probability = Column(Float, nullable=False, default=0.0)
    prediction_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)  # Поле для отслеживания даты создания

    user = relationship("User", back_populates="user_diseases")
    disease = relationship("Disease", back_populates="user_diseases")

# Промежуточная таблица для связи "многие ко многим" между болезнями и симптомами
disease_symptoms = Table(
    "disease_symptoms",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True),
    Column("symptom_id", Integer, ForeignKey("symptoms.id", ondelete="CASCADE"), primary_key=True),
    Column("weight", Float, default=1.0, nullable=False)  # Вес симптома, по умолчанию 1.0
)


# Обновляем связи в классах User и Disease
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    user_diseases = relationship("UserDisease", back_populates="user", cascade="all, delete")  # Обновляем связь
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete")

class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)

    user_diseases = relationship("UserDisease", back_populates="disease")  # Обновляем связь
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
    title = Column(String, nullable=False)  # Новое поле для темы
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
    age_min: Optional[int] = None  # Минимальный возраст (опционально)
    age_max: Optional[int] = None  # Максимальный возраст (опционально)
from pydantic import BaseModel
from typing import Optional

class DiseaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None

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