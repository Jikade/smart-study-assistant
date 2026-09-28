from fastapi import APIRouter

from app.api.v1.routers import (
    analytics,
    auth,
    chat,
    community,
    documents,
    exports,
    flashcards,
    gamification,
    health,
    notifications,
    quizzes,
    study_plans,
    subjects,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(subjects.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(quizzes.router)
api_router.include_router(flashcards.router)
api_router.include_router(study_plans.router)
api_router.include_router(analytics.router)
api_router.include_router(gamification.router)
api_router.include_router(community.router)
api_router.include_router(exports.router)
api_router.include_router(notifications.router)
