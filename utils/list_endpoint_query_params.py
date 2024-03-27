from datetime import date
from typing import Optional
from esmerald import Query, Request
from typing import Annotated

from utils.base_response import (
    SortEnum,
    get_error_response,
)
from utils.base_struct import BaseStruct


class GetSingleParams(BaseStruct):
    load_related: bool = False


class QueryTypeWithoutLoadRelated(BaseStruct):
    filter_string: Optional[str] = None
    page: int = 1
    per_page: int = 10
    order_by: str = "-id"
    export_to_excel: bool = False
    sort_by: SortEnum = SortEnum.DESC
    select: Optional[str] = None


class QueryType(QueryTypeWithoutLoadRelated):
    load_related: bool = False


def query_params(
    filter_string: Annotated[
        str | None,
        Query(
            default="",
            description="Filter through the list of data",
            title="Filter string",
        ),
    ],
    page: Annotated[
        int,
        Query(
            default=1,
            title="paginator page number",
            description="paginator page number for listing the result",
        ),
    ],
    per_page: Annotated[
        int,
        Query(
            default=10,
            title="paginator data per page",
            description="paginator total result per page for listing the result",
        ),
    ],
    order_by: Annotated[
        str,
        Query(
            default="-id",
            title="Order by",
            description="Order the total result to be returned by database columns",
        ),
    ],
    sort_by: Annotated[
        SortEnum,
        Query(
            default=SortEnum.DESC,
            title="Sort By",
            description=f"Sort the total result to be returned by either asc or desc, defaults to {SortEnum.DESC}",
        ),
    ],
    load_related: Annotated[
        bool,
        Query(
            default=False,
            title="Load Related data from database",
            description="Load related data from database particular to each entity, defaults to `False`",
        ),
    ],
    select: Annotated[
        str | None,
        Query(
            default="",
            title="select specific data from database",
            description="Select specific data from this entity, e.g id, name, email. Default to None(meaning select all), it must be a string separated by comma, like `name, id, created_at, updated_at` if the data does not exist in the entitle table it will be returned",
        ),
    ],
):
    return QueryType(
        page=page,
        per_page=per_page,
        order_by=order_by,
        sort_by=sort_by,
        load_related=load_related,
        select=select,
        filter_string=filter_string,
    )


def query_params_without_load_related(
    filter_string: Annotated[
        str | None,
        Query(
            default="",
            description="Filter through the list of data",
            title="Filter string",
        ),
    ],
    page: Annotated[
        int,
        Query(
            default=1,
            title="paginator page number",
            description="paginator page number for listing the result",
        ),
    ],
    per_page: Annotated[
        int,
        Query(
            default=10,
            title="paginator data per page",
            description="paginator total result per page for listing the result",
        ),
    ],
    order_by: Annotated[
        str,
        Query(
            default="-id",
            title="Order by",
            description="Order the total result to be returned by database columns",
        ),
    ],
    sort_by: Annotated[
        SortEnum,
        Query(
            default=SortEnum.DESC,
            title="Sort By",
            description=f"Sort the total result to be returned by either asc or desc, defaults to {SortEnum.DESC}",
        ),
    ],
    select: Annotated[
        str | None,
        Query(
            default="",
            title="select specific data from database",
            description="Select specific data from this entity, e.g id, name, email. Default to None(meaning select all), it must be a string separated by comma, like `name, id, created_at, updated_at` if the data does not exist in the entitle table it will be returned",
        ),
    ],
):
    return QueryTypeWithoutLoadRelated(
        page=page,
        per_page=per_page,
        order_by=order_by,
        sort_by=sort_by,
        select=select,
        filter_string=filter_string,
    )


class ValidateDateFromParams:
    def __init__(self, field_name: str = "date", is_optional=True):
        self.field_name = field_name
        self.is_optional = is_optional

    def parse_date(self, request: Request) -> Optional[date]:
        value = request.query_params.get(self.field_name, None)
        if value is None or value == "" and self.is_optional:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as e:
            raise get_error_response(
                f"{self.field_name} is not a valid date", status_code=422
            ) from e
