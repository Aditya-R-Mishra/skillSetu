import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
from app.models.domain import (
    COLLECTION_USERS,
    COLLECTION_MATERIALS,
    COLLECTION_QUIZZES,
    COLLECTION_QUIZ_ATTEMPTS,
    COLLECTION_COURSE_CATALOG
)

logger = logging.getLogger("skillsetu.database")

# Seed course catalog dataset for MoSPI Official Statistical System domains
MOCK_COURSE_CATALOG = [
    {
        "competency_area": "Survey Design",
        "igot_course_code": "IGOT-SD-101",
        "course_title": "IGOT-SD-101: Advanced Survey Design & Questionnaire Development",
        "description": "Comprehensive course covering questionnaire structuring, field pre-testing, and response bias mitigation in national statistical surveys.",
        "duration": "4 Hours",
        "difficulty": "Intermediate"
    },
    {
        "competency_area": "Data Collection",
        "igot_course_code": "IGOT-DC-201",
        "course_title": "IGOT-DC-201: CAPI Field Survey Methods & Quality Control",
        "description": "Practical guide to Computer-Assisted Personal Interviewing (CAPI), real-time field data validation, and non-sampling error management.",
        "duration": "3.5 Hours",
        "difficulty": "Beginner"
    },
    {
        "competency_area": "Field Methodology",
        "igot_course_code": "IGOT-FM-102",
        "course_title": "IGOT-FM-102: Primary Field Operations & Enumeration Ethics",
        "description": "Protocol for field staff, respondent interaction management, household enumeration tactics, and statistical data confidentiality standards.",
        "duration": "5 Hours",
        "difficulty": "Intermediate"
    },
    {
        "competency_area": "Statistical Analysis",
        "igot_course_code": "IGOT-SA-301",
        "course_title": "IGOT-SA-301: Applied Econometrics & National Account Statistics",
        "description": "Advanced course on calculating GDP estimates, price indices (CPI/WPI), statistical modeling, and data variance analysis for policy makers.",
        "duration": "6 Hours",
        "difficulty": "Advanced"
    },
    {
        "competency_area": "Sampling Techniques",
        "igot_course_code": "IGOT-ST-202",
        "course_title": "IGOT-ST-202: Stratified Multi-Stage Sampling in Large Scale Surveys",
        "description": "In-depth study of probability proportional to size (PPS) sampling, sample design optimization, and weight calibration in MoSPI surveys.",
        "duration": "4.5 Hours",
        "difficulty": "Advanced"
    }
]


class InMemoryCollection:
    """In-Memory Collection Mock providing PyMongo/Motor interface when MongoDB is offline."""
    def __init__(self, name: str):
        self.name = name
        self._docs: List[Dict[str, Any]] = []

    async def create_index(self, keys, unique=False):
        pass

    async def count_documents(self, filter_query: dict) -> int:
        return len(self._filter_docs(filter_query))

    def _filter_docs(self, filter_query: dict) -> List[Dict[str, Any]]:
        results = []
        for d in self._docs:
            match = True
            for k, v in filter_query.items():
                if k == "_id":
                    if str(d.get("_id")) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                results.append(d)
        return results

    async def find_one(self, filter_query: dict) -> Optional[Dict[str, Any]]:
        matches = self._filter_docs(filter_query)
        return matches[0] if matches else None

    async def insert_one(self, doc: dict):
        new_doc = dict(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = ObjectId()
        self._docs.append(new_doc)
        class InsertResult:
            inserted_id = new_doc["_id"]
        return InsertResult()

    async def insert_many(self, docs: List[dict]):
        for d in docs:
            await self.insert_one(d)

    def find(self, filter_query: dict):
        matches = self._filter_docs(filter_query)
        class Cursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction=1):
                return self
            def __aiter__(self):
                self._iter = iter(self.items)
                return self
            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration
            async def to_list(self, length=100):
                return self.items[:length]
        return Cursor(matches)

    def aggregate(self, pipeline: list):
        # Basic aggregate for recommendations / dashboard
        matches = self._docs
        class AggregateCursor:
            def __init__(self, items):
                self.items = items
            async def to_list(self, length=100):
                # group by competency_area
                grouped = {}
                for d in sorted(self.items, key=lambda x: x.get("attempted_at", datetime.min), reverse=True):
                    area = d.get("competency_area", "General Statistical Knowledge")
                    if area not in grouped:
                        grouped[area] = {
                            "_id": area,
                            "latest_score": d.get("score_percent", 0.0),
                            "latest_gap": d.get("gap_level", "Weak")
                        }
                return list(grouped.values())[:length]
        return AggregateCursor(matches)


class InMemoryDatabase:
    """In-Memory Database Mock for resilient offline execution."""
    def __init__(self):
        self.collections = {
            COLLECTION_USERS: InMemoryCollection(COLLECTION_USERS),
            COLLECTION_MATERIALS: InMemoryCollection(COLLECTION_MATERIALS),
            COLLECTION_QUIZZES: InMemoryCollection(COLLECTION_QUIZZES),
            COLLECTION_QUIZ_ATTEMPTS: InMemoryCollection(COLLECTION_QUIZ_ATTEMPTS),
            COLLECTION_COURSE_CATALOG: InMemoryCollection(COLLECTION_COURSE_CATALOG),
        }

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self.collections:
            self.collections[name] = InMemoryCollection(name)
        return self.collections[name]


class Database:
    client: AsyncIOMotorClient = None
    db: Any = None

db_manager = Database()

def get_database() -> Any:
    """Dependency to retrieve database instance. Fallback to in-memory store if DB uninitialized."""
    if db_manager.db is None:
        logger.info("Initializing fallback in-memory database store...")
        db_manager.db = InMemoryDatabase()
        # Seed catalog
        for item in MOCK_COURSE_CATALOG:
            db_manager.db[COLLECTION_COURSE_CATALOG]._docs.append(dict(item))
    return db_manager.db


async def connect_to_mongo():
    """Initializes MongoDB connection and creates indices/seeds data."""
    settings = get_settings()
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
    
    try:
        db_manager.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        db = db_manager.client[settings.DATABASE_NAME]
        
        # Ping
        await db_manager.client.admin.command('ping')
        db_manager.db = db
        logger.info("Successfully connected to live MongoDB server.")
        
        # Setup Indexes
        await db_manager.db[COLLECTION_USERS].create_index("email", unique=True)
        await db_manager.db[COLLECTION_MATERIALS].create_index("user_id")
        await db_manager.db[COLLECTION_QUIZZES].create_index("material_id")
        await db_manager.db[COLLECTION_QUIZ_ATTEMPTS].create_index([("user_id", 1), ("attempted_at", -1)])
        
        # Seed Course Catalog if empty
        catalog_count = await db_manager.db[COLLECTION_COURSE_CATALOG].count_documents({})
        if catalog_count == 0:
            logger.info("Seeding initial iGOT course catalog dataset into MongoDB...")
            await db_manager.db[COLLECTION_COURSE_CATALOG].insert_many(MOCK_COURSE_CATALOG)
            logger.info(f"Seeded {len(MOCK_COURSE_CATALOG)} course catalog items.")
            
    except Exception as e:
        logger.warning(f"Live MongoDB connection unavailable ({e}). Initializing in-memory fallback database.")
        db_manager.db = InMemoryDatabase()
        for item in MOCK_COURSE_CATALOG:
            db_manager.db[COLLECTION_COURSE_CATALOG]._docs.append(dict(item))


async def close_mongo_connection():
    """Closes MongoDB connection on server shutdown."""
    if db_manager.client:
        logger.info("Closing MongoDB connection...")
        db_manager.client.close()
        logger.info("MongoDB connection closed.")
