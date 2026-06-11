from fastapi import APIRouter

from app.api.routes import alerts, analytics, auth, cameras, events, objects, persons, publish, rooms, streaming, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(publish.router)
api_router.include_router(auth.router)
api_router.include_router(rooms.router)
api_router.include_router(cameras.router)
api_router.include_router(streaming.router)
api_router.include_router(streaming.internal_router)
api_router.include_router(objects.router)
api_router.include_router(persons.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)
api_router.include_router(events.router)
