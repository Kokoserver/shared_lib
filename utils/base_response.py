from enum import Enum
from typing import Any
from esmerald import HTTPException, status
from esmerald.datastructures.msgspec import Struct
import msgspec


class SortEnum(Enum):
    ASC = "asc"
    DESC = "desc"


class IHealthCheck(Struct):
    name: str
    version: float
    description: str
    docs_url: str
    redoc_url: str


class IResponseMessage(Struct):
    data: Any
    status_code: int = 200


def get_response(
    data: Any,
    status_code: int = 200,
):
    data_map = {}
    if isinstance(data, Struct):
        data_map = msgspec.structs.asdict(data)
    data_map = data

    return IResponseMessage(
        data=data_map,
        status_code=status_code,
    )


def get_error_response(
    detail: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> HTTPException:
    return HTTPException(
        detail=dict(
            message=detail,
            status_code=status_code,
        ),
        status_code=status_code,
    )


class IFilterList(Struct):
    previous: int | None = None
    next: int | None = None
    total_count: int = 0
    data: set[Any] = set()


class IFilterSingle(Struct):
    data: Any
    status: int


class ICount(Struct):
    count: int = 0


class IError(Struct):
    detail: str
    status_code: int = 401
