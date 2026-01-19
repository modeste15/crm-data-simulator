from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from .db import engine, Base, get_db, SessionLocal
from . import crud
from .models import (
    User,
    Entreprise,
    Interlocuteur,
    Campagne,
    Produit,
    Devis,
    DevisProduit,
    Vente,
)

from .jobs import start_scheduler, stop_scheduler

from .seeders import seed_crm_data


app = FastAPI(title="CRM data simulation POC - FastAPI + Postgres", version="0.1.0")



def reset_public_schema():
    with engine.begin() as conn:
        # Drop tout le schéma public + objets dépendants (tables, index, FK, etc.)
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        # Optionnel: redonner les permissions par défaut
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))



# Helpers: seed demo data
def seed_demo_data(db: Session) -> None:

    # If there's at least one entreprise or user, assume seeded
    has_any = db.scalar(select(User.id).limit(1))
    if has_any:
        return

    # 1) User
    user = User(email="demo@crm.local", full_name="Demo User", phone="0600000000", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2) Entreprise
    ent = Entreprise(
        siren="123456789",
        nom="ACME SAS",
        nb_employe=120,
        cp="75001",
        ville="Paris",
        pays="France",
        secteur="Services",
        website="https://example.com",
        email="contact@acme.local",
        phone="0102030405",
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)

    # 3) Interlocuteur
    inter = Interlocuteur(
        entreprise_id=ent.id,
        first_name="Alice",
        last_name="Martin",
        role="Directrice Achats",
        email="alice.martin@acme.local",
        phone="0611111111",
        is_primary=True,
    )
    db.add(inter)
    db.commit()
    db.refresh(inter)

    # 4) Campagne (optionnelle, utile pour tests)
    camp = Campagne(code="CAMP-2026-001", nom="Campagne Prospection Q1", type="email", is_active=True)
    db.add(camp)
    db.commit()
    db.refresh(camp)

    # 5) Produits
    p1 = Produit(sku="SKU-001", name="Licence CRM - Basic", unit_price=99.00, currency="EUR", is_active=True)
    p2 = Produit(sku="SKU-002", name="Licence CRM - Pro", unit_price=199.00, currency="EUR", is_active=True)
    db.add_all([p1, p2])
    db.commit()
    db.refresh(p1)
    db.refresh(p2)

    # 6) Devis
    devis = Devis(
        owner_id=user.id,
        entreprise_id=ent.id,
        interlocuteur_id=inter.id,
        campagne_id=camp.id,
        code="DEV-2026-0001",
        title="Devis licences CRM",
        status="draft",
        currency="EUR",
        notes="Devis de démonstration",
    )
    db.add(devis)
    db.commit()
    db.refresh(devis)

    # 7) Lignes devis (via CRUD pour recalcul total)
    crud.add_or_update_devis_line(db, devis_id=devis.id, produit_id=p1.id, quantity=3)
    crud.add_or_update_devis_line(db, devis_id=devis.id, produit_id=p2.id, quantity=2)

    # 8) Vente liée au devis (via CRUD)
    crud.create_vente_from_devis(
        db,
        owner_id=user.id,
        entreprise_id=ent.id,
        devis_id=devis.id,
        interlocuteur_id=inter.id,
        campagne_id=camp.id,
        reference="SALE-2026-0001",
        status="open",
        probability=40,
        notes="Vente créée à partir du devis",
    )


@app.on_event("startup")
def on_startup():
    # POC: Supprimer avant de creer  schema
    reset_public_schema()

    Base.metadata.create_all(bind=engine)


    db = SessionLocal()
    try:
        #Seed les données
        seed_crm_data(db, n_users=10, n_entreprises=100, seed=42)
    finally:
        db.close()

    # start scheduler (if you still want hourly inserts for Action/Event you may adapt jobs)
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


# Health
@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# POC endpoints (simple CRUD)

# --- Produits ---
@app.get("/produits")
def list_produits(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return crud.list_produits(db, limit=limit, offset=offset)


@app.post("/produits")
def create_produit(
    sku: str,
    name: str,
    unit_price: float | None = None,
    currency: str = "EUR",
    description: str | None = None,
    db: Session = Depends(get_db),
):
    existing = crud.get_produit_by_sku(db, sku=sku)
    if existing:
        raise HTTPException(status_code=409, detail="SKU already exists")
    return crud.create_produit(db, sku=sku, name=name, unit_price=unit_price, currency=currency, description=description)


@app.get("/produits/{produit_id}")
def get_produit(produit_id: int, db: Session = Depends(get_db)):
    p = crud.get_produit(db, produit_id)
    if not p:
        raise HTTPException(status_code=404, detail="Produit not found")
    return p


@app.delete("/produits/{produit_id}")
def delete_produit(produit_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_produit(db, produit_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Produit not found")
    return {"deleted": True}


# --- Devis ---
@app.get("/devis")
def list_devis(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return crud.list_devis(db, limit=limit, offset=offset)


@app.post("/devis")
def create_devis(
    owner_id: int,
    entreprise_id: int,
    code: str,
    interlocuteur_id: int | None = None,
    campagne_id: int | None = None,
    title: str | None = None,
    status: str = "draft",
    currency: str = "EUR",
    notes: str | None = None,
    db: Session = Depends(get_db),
):
    existing = crud.get_devis_by_code(db, code=code)
    if existing:
        raise HTTPException(status_code=409, detail="Devis code already exists")
    return crud.create_devis(
        db,
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


@app.get("/devis/{devis_id}")
def get_devis(devis_id: int, db: Session = Depends(get_db)):
    d = crud.get_devis(db, devis_id)
    if not d:
        raise HTTPException(status_code=404, detail="Devis not found")
    return d


@app.get("/devis/{devis_id}/lines")
def list_devis_lines(devis_id: int, db: Session = Depends(get_db)):
    d = crud.get_devis(db, devis_id)
    if not d:
        raise HTTPException(status_code=404, detail="Devis not found")
    return crud.list_devis_lines(db, devis_id=devis_id)


@app.post("/devis/{devis_id}/lines")
def add_or_update_devis_line(
    devis_id: int,
    produit_id: int,
    quantity: int = 1,
    unit_price: float | None = None,
    currency: str = "EUR",
    db: Session = Depends(get_db),
):
    line = crud.add_or_update_devis_line(
        db,
        devis_id=devis_id,
        produit_id=produit_id,
        quantity=quantity,
        unit_price=unit_price,
        currency=currency,
    )
    if not line:
        raise HTTPException(status_code=404, detail="Devis or Produit not found")
    return line


@app.delete("/devis/{devis_id}/lines/{produit_id}")
def remove_devis_line(devis_id: int, produit_id: int, db: Session = Depends(get_db)):
    ok = crud.remove_devis_line(db, devis_id=devis_id, produit_id=produit_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Line not found")
    return {"deleted": True}


# --- Ventes ---
@app.get("/ventes")
def list_ventes(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return crud.list_ventes(db, limit=limit, offset=offset)


@app.post("/ventes/from-devis")
def create_vente_from_devis(
    owner_id: int,
    entreprise_id: int,
    devis_id: int,
    interlocuteur_id: int | None = None,
    campagne_id: int | None = None,
    reference: str | None = None,
    status: str = "open",
    probability: int | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
):
    v = crud.create_vente_from_devis(
        db,
        owner_id=owner_id,
        entreprise_id=entreprise_id,
        devis_id=devis_id,
        interlocuteur_id=interlocuteur_id,
        campagne_id=campagne_id,
        reference=reference,
        status=status,
        probability=probability,
        notes=notes,
    )
    if not v:
        raise HTTPException(status_code=404, detail="Devis not found")
    return v


@app.get("/ventes/{vente_id}")
def get_vente(vente_id: int, db: Session = Depends(get_db)):
    v = crud.get_vente(db, vente_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vente not found")
    return v
