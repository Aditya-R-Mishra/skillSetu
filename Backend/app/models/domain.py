import sys
from typing import Any
from bson import ObjectId

class PyObjectId(str):
    """
    Custom type for validating MongoDB BSON ObjectIds in Pydantic models.
    Converts ObjectId to string and vice versa seamlessly.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value: Any) -> str:
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return value
        raise ValueError(f"Invalid ObjectId: {value}")


# Collection Constants
COLLECTION_USERS = "users"
COLLECTION_MATERIALS = "materials"
COLLECTION_QUIZZES = "quizzes"
COLLECTION_QUIZ_ATTEMPTS = "quiz_attempts"
COLLECTION_COURSE_CATALOG = "course_catalog"
