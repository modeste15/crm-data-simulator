from __future__ import annotations

from typing import Optional, List
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import Produit, Devis, DevisProduit, Vente


# PRODUITS CRUD
def create_produit(
    db: Session,
    sku: str,
    name: str,
    unit_price: Optional[Decimal] = None,
    currency: str = "EUR",
    description: Optional[str] = None,
) -> Produit:
    p = Produit(
        sku=sku,
        name=name,
        unit_price=unit_price,
        currency=currency,
        description=description,
        is_active=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_produit(db: Session, produit_id: int) -> Optional[Produit]:
    return db.get(Produit, produit_id)


def get_produit_by_sku(db: Session, sku: str) -> Optional[Produit]:
    return db.scalar(select(Produit).where(Produit.sku == sku))


def list_produits(db: Session, limit: int = 50, offset: int = 0) -> List[Produit]:
    return list(db.scalars(select(Produit).order_by(Produit.id.desc()).offset(offset).limit(limit)))


def update_produit(
    db: Session,
    produit_id: int,
    *,
    name: Optional[str] = None,
    unit_price: Optional[Decimal] = None,
    currency: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[Produit]:
    p = db.get(Produit, produit_id)
    if not p:
        return None

    if name is not None:
        p.name = name
    if unit_price is not None:
        p.unit_price = unit_price
    if currency is not None:
        p.currency = currency
    if description is not None:
        p.description = description
    if is_active is not None:
        p.is_active = is_active

    db.commit()
    db.refresh(p)
    return p


def delete_produit(db: Session, produit_id: int) -> bool:
    p = db.get(Produit, produit_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True


# DEVIS CRUD
def create_devis(
    db: Session,
    *,
    owner_id: int,
    entreprise_id: int,
    code: str,
    interlocuteur_id: Optional[int] = None,
    campagne_id: Optional[int] = None,
    title: Optional[str] = None,
    status: str = "draft",
    currency: str = "EUR",
    notes: Optional[str] = None,
) -> Devis:
    d = Devis(
        owner_id=owner_id,
        entreprise_id=entreprise_id,
        interlocuteur_id=interlocuteur_id,
        campagne_id=campagne_id,
        code=code,
        title=title,
        status=status,
        currency=currency,
        notes=notes,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def get_devis(db: Session, devis_id: int) -> Optional[Devis]:
    return db.get(Devis, devis_id)


def get_devis_by_code(db: Session, code: str) -> Optional[Devis]:
    return db.scalar(select(Devis).where(Devis.code == code))


def list_devis(db: Session, limit: int = 50, offset: int = 0) -> List[Devis]:
    return list(db.scalars(select(Devis).order_by(Devis.id.desc()).offset(offset).limit(limit)))


def update_devis(
    db: Session,
    devis_id: int,
    *,
    title: Optional[str] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    issue_date: Optional[object] = None,  # date
    valid_until: Optional[object] = None,  # date
    interlocuteur_id: Optional[int] = None,
    campagne_id: Optional[int] = None,
) -> Optional[Devis]:
    d = db.get(Devis, devis_id)
    if not d:
        return None

    if title is not None:
        d.title = title
    if status is not None:
        d.status = status
    if notes is not None:
        d.notes = notes
    if issue_date is not None:
        d.issue_date = issue_date
    if valid_until is not None:
        d.valid_until = valid_until
    if interlocuteur_id is not None:
        d.interlocuteur_id = interlocuteur_id
    if campagne_id is not None:
        d.campagne_id = campagne_id

    db.commit()
    db.refresh(d)
    return d


def delete_devis(db: Session, devis_id: int) -> bool:
    d = db.get(Devis, devis_id)
    if not d:
        return False
    db.delete(d)
    db.commit()
    return True


# LIGNES DE DEVIS (DevisProduit) CRUD
def _compute_line_total(quantity: int, unit_price: Optional[Decimal]) -> Optional[Decimal]:
    if unit_price is None:
        return None
    return Decimal(quantity) * Decimal(unit_price)


def _recompute_devis_total(db: Session, devis_id: int) -> None:
    d = db.get(Devis, devis_id)
    if not d:
        return

    total = Decimal("0.00")
    has_any = False
    for line in d.lines:
        if line.line_total is not None:
            total += Decimal(line.line_total)
            has_any = True

    d.total_amount = total if has_any else None
    db.commit()


def add_or_update_devis_line(
    db: Session,
    *,
    devis_id: int,
    produit_id: int,
    quantity: int = 1,
    unit_price: Optional[Decimal] = None,
    currency: str = "EUR",
) -> Optional[DevisProduit]:
    d = db.get(Devis, devis_id)
    if not d:
        return None

    p = db.get(Produit, produit_id)
    if not p:
        return None

    # si unit_price non fourni => prix du produit (si existant)
    if unit_price is None and p.unit_price is not None:
        unit_price = Decimal(p.unit_price)

    line = db.scalar(
        select(DevisProduit).where(
            DevisProduit.devis_id == devis_id,
            DevisProduit.produit_id == produit_id,
        )
    )

    if line:
        line.quantity = quantity
        line.unit_price = unit_price
        line.currency = currency
        line.line_total = _compute_line_total(quantity, unit_price)
    else:
        line = DevisProduit(
            devis_id=devis_id,
            produit_id=produit_id,
            quantity=quantity,
            unit_price=unit_price,
            currency=currency,
            line_total=_compute_line_total(quantity, unit_price),
        )
        db.add(line)

    db.commit()
    db.refresh(line)

    _recompute_devis_total(db, devis_id)
    return line


def remove_devis_line(db: Session, *, devis_id: int, produit_id: int) -> bool:
    line = db.scalar(
        select(DevisProduit).where(
            DevisProduit.devis_id == devis_id,
            DevisProduit.produit_id == produit_id,
        )
    )
    if not line:
        return False

    db.delete(line)
    db.commit()

    _recompute_devis_total(db, devis_id)
    return True


def list_devis_lines(db: Session, devis_id: int) -> List[DevisProduit]:
    return list(db.scalars(select(DevisProduit).where(DevisProduit.devis_id == devis_id)))


# VENTES CRUD (liée à un devis)
def create_vente_from_devis(
    db: Session,
    *,
    owner_id: int,
    entreprise_id: int,
    devis_id: int,
    interlocuteur_id: Optional[int] = None,
    campagne_id: Optional[int] = None,
    reference: Optional[str] = None,
    status: str = "open",
    probability: Optional[int] = None,
    expected_close_date: Optional[object] = None,  # date
    notes: Optional[str] = None,
) -> Optional[Vente]:
    d = db.get(Devis, devis_id)
    if not d:
        return None

    # 1 vente max par devis (UniqueConstraint + check logique)
    existing = db.scalar(select(Vente).where(Vente.devis_id == devis_id))
    if existing:
        return existing

    # amount par défaut = total du devis si dispo
    amount = d.total_amount

    v = Vente(
        owner_id=owner_id,
        entreprise_id=entreprise_id,
        interlocuteur_id=interlocuteur_id,
        campagne_id=campagne_id,
        devis_id=devis_id,
        reference=reference,
        amount=amount,
        currency=d.currency,
        status=status,
        probability=probability,
        expected_close_date=expected_close_date,
        notes=notes,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def get_vente(db: Session, vente_id: int) -> Optional[Vente]:
    return db.get(Vente, vente_id)


def list_ventes(db: Session, limit: int = 50, offset: int = 0) -> List[Vente]:
    return list(db.scalars(select(Vente).order_by(Vente.id.desc()).offset(offset).limit(limit)))


def update_vente(
    db: Session,
    vente_id: int,
    *,
    status: Optional[str] = None,
    probability: Optional[int] = None,
    expected_close_date: Optional[object] = None,  # date
    closed_at: Optional[object] = None,  # datetime
    notes: Optional[str] = None,
) -> Optional[Vente]:
    v = db.get(Vente, vente_id)
    if not v:
        return None

    if status is not None:
        v.status = status
    if probability is not None:
        v.probability = probability
    if expected_close_date is not None:
        v.expected_close_date = expected_close_date
    if closed_at is not None:
        v.closed_at = closed_at
    if notes is not None:
        v.notes = notes

    db.commit()
    db.refresh(v)
    return v


def delete_vente(db: Session, vente_id: int) -> bool:
    v = db.get(Vente, vente_id)
    if not v:
        return False
    db.delete(v)
    db.commit()
    return True
