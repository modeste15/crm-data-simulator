from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import (
    User,
    Entreprise,
    Interlocuteur,
    Campagne,
    Produit,
    Devis,
    DevisProduit,
    Vente,
    Action,
)


def _rand_phone() -> str:
    return "0" + "".join(str(random.randint(0, 9)) for _ in range(9))


def _rand_cp() -> str:
    return str(random.randint(1000, 95999)).zfill(5)


def _rand_siren(existing: set[str]) -> str:
    # SIREN: 9 chiffres (string). On évite les doublons.
    while True:
        s = "".join(str(random.randint(0, 9)) for _ in range(9))
        if s not in existing:
            existing.add(s)
            return s


def _pick(seq):
    return seq[random.randint(0, len(seq) - 1)]


def seed_crm_data(
    db: Session,
    *,
    n_users: int = 10,
    n_entreprises: int = 100,
    seed: int = 42,
) -> None:
    """
    Seed complet CRM:
      - 10 users
      - 100 entreprises
      - interlocuteurs (1-3 / entreprise)
      - campagnes (quelques-unes)
      - produits (quelques-uns)
      - devis + lignes
      - ventes (liées à devis)
      - actions (avec ou sans campagne)

    Garde-fou: si au moins 1 user existe, on ne reseed pas.
    """
    random.seed(seed)

    # Garde-fou simple
    has_user = db.scalar(select(User.id).limit(1))
    if has_user:
        return

    # ----------------------------
    # USERS
    # ----------------------------
    users: list[User] = []
    for i in range(n_users):
        u = User(
            email=f"user{i+1}@crm.local",
            full_name=f"User {i+1}",
            phone=_rand_phone(),
            is_active=True,
        )
        db.add(u)
        users.append(u)
    db.commit()
    for u in users:
        db.refresh(u)

    # ----------------------------
    # CAMPAGNES
    # ----------------------------
    campagne_types = ["email", "call", "linkedin", "webinar", "ads"]
    campagnes: list[Campagne] = []
    for i in range(6):
        c = Campagne(
            code=f"CAMP-2026-{(i+1):03d}",
            nom=f"Campagne {(i+1)}",
            type=_pick(campagne_types),
            is_active=True,
        )
        db.add(c)
        campagnes.append(c)
    db.commit()
    for c in campagnes:
        db.refresh(c)

    # ----------------------------
    # PRODUITS
    # ----------------------------
    produits: list[Produit] = []
    product_names = [
        "Licence CRM - Basic",
        "Licence CRM - Pro",
        "Module Reporting",
        "Module Automatisation",
        "Intégration API",
        "Support Premium",
    ]
    for i, name in enumerate(product_names, start=1):
        p = Produit(
            sku=f"SKU-{i:03d}",
            name=name,
            description=f"Produit: {name}",
            unit_price=random.choice([49.0, 99.0, 199.0, 299.0, 499.0]),
            currency="EUR",
            is_active=True,
        )
        db.add(p)
        produits.append(p)
    db.commit()
    for p in produits:
        db.refresh(p)

    # ----------------------------
    # ENTREPRISES + INTERLOCUTEURS
    # ----------------------------
    secteurs = ["Retail", "Services", "Finance", "Industrie", "Tech", "Santé", "Éducation"]
    villes = ["Paris", "Lyon", "Marseille", "Nantes", "Lille", "Bordeaux", "Toulouse"]
    pays = "France"

    sirens = set()
    entreprises: list[Entreprise] = []
    interlocuteurs: list[Interlocuteur] = []

    for i in range(n_entreprises):
        ent = Entreprise(
            siren=_rand_siren(sirens),
            nom=f"Entreprise {i+1} {uuid.uuid4().hex[:6].upper()}",
            nb_employe=random.randint(1, 5000),
            cp=_rand_cp(),
            ville=_pick(villes),
            pays=pays,
            secteur=_pick(secteurs),
            website=f"https://entreprise{i+1}.example.com",
            email=f"contact{i+1}@entreprises.local",
            phone=_rand_phone(),
        )
        db.add(ent)
        entreprises.append(ent)

    db.commit()
    for ent in entreprises:
        db.refresh(ent)

    # Interlocuteurs 1 à 3 / entreprise
    last_names = ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois"]
    first_names = ["Alice", "Bob", "Chloé", "David", "Emma", "Fares", "Inès", "Jules"]
    roles = ["CEO", "DAF", "DSI", "Directeur Achats", "Directeur Commercial", "RH"]

    for ent in entreprises:
        k = random.randint(1, 3)
        for j in range(k):
            inter = Interlocuteur(
                entreprise_id=ent.id,
                first_name=_pick(first_names),
                last_name=_pick(last_names),
                role=_pick(roles),
                email=f"{uuid.uuid4().hex[:8]}@{ent.nom.replace(' ', '').lower()}.local",
                phone=_rand_phone(),
                is_primary=(j == 0),
            )
            db.add(inter)
            interlocuteurs.append(inter)

    db.commit()
    # refresh en masse pas obligatoire pour usage FK (on a id après commit), mais ok si tu veux
    # for inter in interlocuteurs: db.refresh(inter)

    # Map entreprise -> interlocuteurs
    inter_by_ent: dict[int, list[Interlocuteur]] = {}
    for inter in interlocuteurs:
        inter_by_ent.setdefault(inter.entreprise_id, []).append(inter)

    # ----------------------------
    # DEVIS + LIGNES + VENTES
    # ----------------------------
    devis_list: list[Devis] = []
    ventes_list: list[Vente] = []

    # On crée ~ 1 devis sur 2 entreprises
    for idx, ent in enumerate(entreprises):
        if idx % 2 == 1:
            continue

        owner = _pick(users)
        inter = _pick(inter_by_ent[ent.id])
        camp = _pick(campagnes) if random.random() < 0.7 else None

        code = f"DEV-2026-{idx+1:04d}"
        d = Devis(
            owner_id=owner.id,
            entreprise_id=ent.id,
            interlocuteur_id=inter.id,
            campagne_id=(camp.id if camp else None),
            code=code,
            title=f"Devis - {ent.nom}",
            status=random.choice(["draft", "sent", "accepted", "rejected"]),
            issue_date=date.today() - timedelta(days=random.randint(0, 60)),
            valid_until=date.today() + timedelta(days=random.randint(10, 90)),
            currency="EUR",
            notes="Seeded devis",
        )
        db.add(d)
        devis_list.append(d)

    db.commit()
    for d in devis_list:
        db.refresh(d)

    # Lignes devis: 1 à 4 produits
    for d in devis_list:
        n_lines = random.randint(1, 4)
        chosen = random.sample(produits, k=min(n_lines, len(produits)))

        total = 0.0
        for p in chosen:
            qty = random.randint(1, 10)
            unit_price = float(p.unit_price) if p.unit_price is not None else random.choice([49.0, 99.0, 199.0])
            line_total = qty * unit_price
            total += line_total

            line = DevisProduit(
                devis_id=d.id,
                produit_id=p.id,
                quantity=qty,
                unit_price=unit_price,
                currency="EUR",
                line_total=line_total,
            )
            db.add(line)

        # cache total dans devis (tu peux préférer recalcul dynamique)
        d.total_amount = total

    db.commit()

    # Ventes: pour les devis "accepted" (ou une partie)
    for d in devis_list:
        if d.status == "accepted" and random.random() < 0.9:
            v = Vente(
                owner_id=d.owner_id,
                entreprise_id=d.entreprise_id,
                interlocuteur_id=d.interlocuteur_id,
                campagne_id=d.campagne_id,
                devis_id=d.id,
                reference=f"SALE-2026-{d.id:05d}",
                amount=d.total_amount,
                currency=d.currency,
                status=random.choice(["open", "won"]),
                probability=random.choice([30, 50, 70, 90]),
                expected_close_date=date.today() + timedelta(days=random.randint(5, 45)),
                notes="Seeded vente from accepted devis",
            )
            db.add(v)
            ventes_list.append(v)

    db.commit()

    # ----------------------------
    # ACTIONS (avec ou sans campagne)
    # ----------------------------
    action_kinds = ["call", "email", "meeting", "linkedin"]
    action_statuses = ["todo", "done", "canceled"]

    # volume actions: ~ 4 actions / entreprise
    now = datetime.now()
    for ent in entreprises:
        owner = _pick(users)
        inter = _pick(inter_by_ent[ent.id])
        for _ in range(4):
            camp = _pick(campagnes) if random.random() < 0.5 else None
            due = now + timedelta(days=random.randint(-10, 20), hours=random.randint(0, 23))
            st = _pick(action_statuses)
            done_at = (due + timedelta(hours=1)) if st == "done" else None

            a = Action(
                owner_id=owner.id,
                entreprise_id=ent.id,
                interlocuteur_id=inter.id if random.random() < 0.9 else None,
                campagne_id=camp.id if camp else None,
                kind=_pick(action_kinds),
                status=st,
                title=f"Action {_pick(action_kinds)} - {ent.nom}",
                notes="Seeded action",
                due_at=due,
                done_at=done_at,
            )
            db.add(a)

    db.commit()
