from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import Flashcard, FlashcardDeck, FlashcardProgress
from app.schemas.flashcards import DeckCreate, DeckGenerateRequest, DeckOut, FlashcardOut, ProgressOut, ReviewRequest
from app.services.flashcard_service import create_deck, generate_deck, review_flashcard

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


def visible_deck(db: DbSession, user_id: int, deck_id: int) -> FlashcardDeck:
    deck = db.get(FlashcardDeck, deck_id)
    if deck is None or (deck.owner_id != user_id and deck.visibility not in {"PUBLIC", "UNLISTED"}):
        raise HTTPException(404, "Flashcard deck not found")
    return deck


@router.get("/decks", response_model=list[DeckOut])
def list_decks(db: DbSession, user: CurrentUser, limit: int = 50):
    return list(db.scalars(select(FlashcardDeck).where(FlashcardDeck.owner_id == user.id).order_by(FlashcardDeck.created_at.desc()).limit(limit)).all())


@router.post("/decks", response_model=DeckOut, status_code=201)
def create(payload: DeckCreate, db: DbSession, user: CurrentUser):
    return create_deck(db, user.id, payload)


@router.post("/decks/generate", response_model=DeckOut, status_code=201)
def generate(payload: DeckGenerateRequest, db: DbSession, user: CurrentUser):
    return generate_deck(db, user.id, payload)


@router.get("/decks/{deck_id}")
def get_deck(deck_id: int, db: DbSession, user: CurrentUser):
    deck = visible_deck(db, user.id, deck_id)
    cards = list(db.scalars(select(Flashcard).where(Flashcard.deck_id == deck.id).order_by(Flashcard.card_order)).all())
    return {**DeckOut.model_validate(deck).model_dump(), "cards": [FlashcardOut.model_validate(c).model_dump() for c in cards]}


@router.get("/due", response_model=list[FlashcardOut])
def due_cards(db: DbSession, user: CurrentUser, limit: int = 50):
    now = datetime.now(timezone.utc)
    stmt = (
        select(Flashcard)
        .join(FlashcardDeck, FlashcardDeck.id == Flashcard.deck_id)
        .outerjoin(FlashcardProgress, (FlashcardProgress.flashcard_id == Flashcard.id) & (FlashcardProgress.user_id == user.id))
        .where(FlashcardDeck.owner_id == user.id)
        .where((FlashcardProgress.user_id.is_(None)) | (FlashcardProgress.next_review_at <= now))
        .order_by(FlashcardProgress.next_review_at.asc().nullsfirst(), Flashcard.id)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@router.post("/{flashcard_id}/review", response_model=ProgressOut)
def review(flashcard_id: int, payload: ReviewRequest, db: DbSession, user: CurrentUser):
    card = db.get(Flashcard, flashcard_id)
    if card is None:
        raise HTTPException(404, "Flashcard not found")
    deck = visible_deck(db, user.id, card.deck_id)
    return review_flashcard(db, user.id, card, payload.rating, payload.response_time_ms)
