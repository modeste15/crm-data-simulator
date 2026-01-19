from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# COMMON
class ORMBase(BaseModel):
    model_config = {"from_attributes": True}


# USERS
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=30)
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=30)
    is_active: Optional[bool] = None


class UserOut(ORMBase):
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ENTREPRISES
class EntrepriseCreate(BaseModel):
    siren: str = Field(min_length=9, max_length=9)
    nom: str = Field(min_length=1, max_length=255)
    nb_employe: Optional[int] = None
    cp: Optional[str] = Field(default=None, max_length=10)
    ville: Optional[str] = Field(default=None, max_length=100)
    pays: Optional[str] = Field(default=None, max_length=80)
    secteur: Optional[str] = Field(default=None, max_length=120)
    website: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)


class EntrepriseUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, max_length=255)
    nb_employe: Optional[int] = None
    cp: Optional[str] = Field(default=None, max_length=10)
    ville: Optional[str] = Field(default=None, max_length=100)
    pays: Optional[str] = Field(default=None, max_length=80)
    secteur: Optional[str] = Field(default=None, max_length=120)
    website: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)


class EntrepriseOut(ORMBase):
    id: int
    siren: str
    nom: str
    nb_employe: Optional[int]
    cp: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    secteur: Optional[str]
    website: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime


# INTERLOCUTEURS
class InterlocuteurCreate(BaseModel):
    entreprise_id: int
    first_name: Optional[str] = Field(default=None, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    role: Optional[str] = Field(default=None, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    is_primary: bool = False


class InterlocuteurUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=120)
    last_name: Optional[str] = Field(default=None, max_length=120)
    role: Optional[str] = Field(default=None, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    is_primary: Optional[bool] = None


class InterlocuteurOut(ORMBase):
    id: int
    entreprise_id: int
    first_name: Optional[str]
    last_name: str
    role: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_primary: bool
    created_at: datetime
    updated_at: datetime


# CAMPAGNES
class CampagneCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    nom: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=60)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True


class CampagneUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, max_length=255)
    type: Optional[str] = Field(default=None, max_length=60)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class CampagneOut(ORMBase):
    id: int
    code: str
    nom: str
    type: str
    start_date: Optional[date]
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# PRODUITS
class ProduitCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    unit_price: Optional[float] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    is_active: bool = True


class ProduitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    is_active: Optional[bool] = None


class ProduitOut(ORMBase):
    id: int
    sku: str
    name: str
    description: Optional[str]
    unit_price: Optional[float]
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DevisLineUpsert(BaseModel):
    produit_id: int
    quantity: int = Field(default=1, ge=1)
    unit_price: Optional[float] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class DevisProduitOut(ORMBase):
    id: int
    devis_id: int
    produit_id: int
    quantity: int
    unit_price: Optional[float]
    currency: str
    line_total: Optional[float]
    created_at: datetime


class DevisCreate(BaseModel):
    owner_id: int
    entreprise_id: int
    code: str = Field(min_length=1, max_length=80)
    interlocuteur_id: Optional[int] = None
    campagne_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="draft", max_length=30)
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    lines: Optional[List[DevisLineUpsert]] = None  # pratique pour create avec lignes


class DevisUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=30)
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    interlocuteur_id: Optional[int] = None
    campagne_id: Optional[int] = None


class DevisOut(ORMBase):
    id: int
    owner_id: int
    entreprise_id: int
    interlocuteur_id: Optional[int]
    campagne_id: Optional[int]
    code: str
    title: Optional[str]
    status: str
    issue_date: Optional[date]
    valid_until: Optional[date]
    notes: Optional[str]
    total_amount: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime
    lines: List[DevisProduitOut] = []


# VENTES
class VenteCreateFromDevis(BaseModel):
    owner_id: int
    entreprise_id: int
    devis_id: int
    interlocuteur_id: Optional[int] = None
    campagne_id: Optional[int] = None
    reference: Optional[str] = Field(default=None, max_length=80)
    status: str = Field(default="open", max_length=30)
    probability: Optional[int] = Field(default=None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    notes: Optional[str] = None


class VenteUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=30)
    probability: Optional[int] = Field(default=None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None


class VenteOut(ORMBase):
    id: int
    owner_id: int
    entreprise_id: int
    interlocuteur_id: Optional[int]
    campagne_id: Optional[int]
    devis_id: int
    reference: Optional[str]
    amount: Optional[float]
    currency: str
    status: str
    probability: Optional[int]
    expected_close_date: Optional[date]
    closed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ACTIONS
class ActionCreate(BaseModel):
    owner_id: int
    entreprise_id: int
    interlocuteur_id: Optional[int] = None
    campagne_id: Optional[int] = None
    kind: str = Field(min_length=1, max_length=40)     # call/email/meeting...
    status: str = Field(default="todo", max_length=30)  # todo/done/...
    title: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    due_at: Optional[datetime] = None
    done_at: Optional[datetime] = None


class ActionUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=30)
    title: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    due_at: Optional[datetime] = None
    done_at: Optional[datetime] = None
    campagne_id: Optional[int] = None
    interlocuteur_id: Optional[int] = None


class ActionOut(ORMBase):
    id: int
    owner_id: int
    entreprise_id: int
    interlocuteur_id: Optional[int]
    campagne_id: Optional[int]
    kind: str
    status: str
    title: Optional[str]
    notes: Optional[str]
    due_at: Optional[datetime]
    done_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
