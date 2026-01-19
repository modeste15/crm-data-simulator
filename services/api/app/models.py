from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    String,
    DateTime,
    Date,
    Boolean,
    Integer,
    Numeric,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# USERS
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    actions: Mapped[List["Action"]] = relationship(back_populates="owner", cascade="all,delete-orphan")
    devis: Mapped[List["Devis"]] = relationship(back_populates="owner", cascade="all,delete-orphan")
    ventes: Mapped[List["Vente"]] = relationship(back_populates="owner", cascade="all,delete-orphan")


# ENTREPRISES
class Entreprise(Base):
    __tablename__ = "entreprises"
    __table_args__ = (
        UniqueConstraint("siren", name="uq_entreprises_siren"),
        #Index("ix_entreprises_cp", "cp"),
        #Index("ix_entreprises_nom", "nom"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    siren: Mapped[str] = mapped_column(String(9), nullable=False)
    nom: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    nb_employe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cp: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    ville: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pays: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    secteur: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    interlocuteurs: Mapped[List["Interlocuteur"]] = relationship(
        back_populates="entreprise", cascade="all,delete-orphan"
    )
    actions: Mapped[List["Action"]] = relationship(back_populates="entreprise")
    devis: Mapped[List["Devis"]] = relationship(back_populates="entreprise")
    ventes: Mapped[List["Vente"]] = relationship(back_populates="entreprise")


# INTERLOCUTEURS
class Interlocuteur(Base):
    __tablename__ = "interlocuteurs"
    __table_args__ = (
        Index("ix_interlocuteurs_email", "email"),
        Index("ix_interlocuteurs_nom", "last_name", "first_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    entreprise_id: Mapped[int] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False, index=True)

    first_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)

    role: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    entreprise: Mapped["Entreprise"] = relationship(back_populates="interlocuteurs")
    actions: Mapped[List["Action"]] = relationship(back_populates="interlocuteur")
    devis: Mapped[List["Devis"]] = relationship(back_populates="interlocuteur")
    ventes: Mapped[List["Vente"]] = relationship(back_populates="interlocuteur")


# CAMPAGNES
class Campagne(Base):
    __tablename__ = "campagnes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_campagnes_code"),
        Index("ix_campagnes_type", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(60), nullable=False)

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    actions: Mapped[List["Action"]] = relationship(back_populates="campagne")
    devis: Mapped[List["Devis"]] = relationship(back_populates="campagne")
    ventes: Mapped[List["Vente"]] = relationship(back_populates="campagne")


# PRODUITS
class Produit(Base):
    __tablename__ = "produits"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_produits_sku"),
        Index("ix_produits_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sku: Mapped[str] = mapped_column(String(80), nullable=False)   # référence produit
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    devis_lines: Mapped[List["DevisProduit"]] = relationship(back_populates="produit")


# DEVIS
class Devis(Base):
    __tablename__ = "devis"
    __table_args__ = (
        UniqueConstraint("code", name="uq_devis_code"),
        Index("ix_devis_status", "status"),
        Index("ix_devis_issue_date", "issue_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    entreprise_id: Mapped[int] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False, index=True)
    interlocuteur_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interlocuteurs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campagne_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campagnes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    code: Mapped[str] = mapped_column(String(80), nullable=False)  # ex: DEV-2026-0001
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft/sent/accepted/rejected/expired
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # total peut être recalculé à partir des lignes; on le garde optionnel (cache)
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="devis")
    entreprise: Mapped["Entreprise"] = relationship(back_populates="devis")
    interlocuteur: Mapped[Optional["Interlocuteur"]] = relationship(back_populates="devis")
    campagne: Mapped[Optional["Campagne"]] = relationship(back_populates="devis")

    lines: Mapped[List["DevisProduit"]] = relationship(
        back_populates="devis", cascade="all,delete-orphan"
    )
    vente: Mapped[Optional["Vente"]] = relationship(back_populates="devis", uselist=False)

class DevisProduit(Base):
    __tablename__ = "devis_produits"
    __table_args__ = (
        UniqueConstraint("devis_id", "produit_id", name="uq_devis_produit"),
        Index("ix_devis_produits_devis_id", "devis_id"),
        Index("ix_devis_produits_produit_id", "produit_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id", ondelete="CASCADE"), nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produits.id", ondelete="RESTRICT"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)  # prix figé sur le devis
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    line_total: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    devis: Mapped["Devis"] = relationship(back_populates="lines")
    produit: Mapped["Produit"] = relationship(back_populates="devis_lines")


# ACTIONS (liée à campagne ou non + interlocuteur)
class Action(Base):
    __tablename__ = "actions"
    __table_args__ = (
        Index("ix_actions_kind", "kind"),
        Index("ix_actions_status", "status"),
        Index("ix_actions_due_at", "due_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    entreprise_id: Mapped[int] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False, index=True)
    interlocuteur_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interlocuteurs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    campagne_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campagnes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="todo", nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="actions")
    entreprise: Mapped["Entreprise"] = relationship(back_populates="actions")
    interlocuteur: Mapped[Optional["Interlocuteur"]] = relationship(back_populates="actions")
    campagne: Mapped[Optional["Campagne"]] = relationship(back_populates="actions")


# VENTES (liée à un devis)
class Vente(Base):
    __tablename__ = "ventes"
    __table_args__ = (
        UniqueConstraint("devis_id", name="uq_ventes_devis_id"),  # 1 vente par devis
        Index("ix_ventes_status", "status"),
        Index("ix_ventes_closed_at", "closed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    entreprise_id: Mapped[int] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False, index=True)
    interlocuteur_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interlocuteurs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campagne_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campagnes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id", ondelete="RESTRICT"), nullable=False, index=True)

    reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)

    amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)  # open, won, lost, canceled
    probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0..100
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="ventes")
    entreprise: Mapped["Entreprise"] = relationship(back_populates="ventes")
    interlocuteur: Mapped[Optional["Interlocuteur"]] = relationship(back_populates="ventes")
    campagne: Mapped[Optional["Campagne"]] = relationship(back_populates="ventes")
    devis: Mapped["Devis"] = relationship(back_populates="vente")
