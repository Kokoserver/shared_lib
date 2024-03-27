import io
from dataclasses import dataclass
import msgspec
from typing import List, TypeVar, Generic
import uuid
from saffier import Model, QuerySet

from esmerald.responses import StreamingResponse
from esmerald import AsyncDAOProtocol, status
from esmerald.datastructures.msgspec import Struct
import openpyxl
from esmerald_utils.utils.base_response import (
    ICount,
    IFilterList,
    IFilterSingle,
    SortEnum,
    get_error_response,
)

from typing import List, Optional


ModelType = TypeVar("ModelType", bound=Model)


@dataclass(slots=True, kw_only=True)
class BaseRepository(
    AsyncDAOProtocol,
    Generic[ModelType],
):
    model: ModelType | None = None
    model_name: str = "Object"

    @property
    def get_related(self) -> set[str]:
        return set.union(
            self.model.meta.foreign_key_fields.keys(),
            self.model.meta.many_to_many_fields,
        )

    @property
    def get_related_backward(self) -> set[str]:
        return set.union(
            self.model.meta.related_fields.keys(),
        )

    @property
    def query(self) -> QuerySet:
        return self.model

    async def get_single(
        self,
        object_id: str,
        and_check: dict = None,
        or_check: list = None,
        load_related: bool = False,
        raise_error: bool = True,
        object_only: bool = False,
    ) -> IFilterSingle | ModelType:
        if and_check is None:
            and_check = {}
        if or_check is None:
            or_check = []
        query = self.query.filter(id=object_id)
        if or_check:
            query = query.or_(**or_check)
        if and_check:
            query = query.and_(**and_check)
        if load_related:
            query = query.prefetch_related(
                *self.get_related,
                *self.get_related_backward,
            )

        query = query.order_by("-id")
        raw_result = await query.first()

        if not raw_result and raise_error:
            raise get_error_response(
                detail=f"{self.model_name} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        elif not raw_result:
            return raw_result
        if object_only:
            return raw_result
        if load_related:
            results = await self.to_dict(raw_result=[raw_result])
            if len(results) > 0:
                raw_result = results.pop(0)
        else:
            raw_result = dict(raw_result)
        return IFilterSingle(data=raw_result, status=200)

    async def to_dict(self, raw_result: list[Model]) -> list[dict]:
        columns = (*self.get_related, *self.get_related_backward)
        return [
            {
                **{
                    field_name: [
                        dict(data) for data in list(getattr(result, field_name))
                    ]
                    for field_name in self.model.meta.many_to_many_fields
                    if hasattr(result, field_name)
                },
                **{
                    field_name: dict(getattr(result, field_name))
                    for field_name in self.model.meta.foreign_key_fields.keys()
                    if hasattr(result, field_name) and getattr(result, field_name)
                },
                **{
                    field_name: dict(getattr(result, field_name, {}))
                    for field_name in self.model.meta.foreign_key_fields.keys()
                    if hasattr(result, field_name) and getattr(result, field_name)
                },
                **{
                    attr: getattr(result, attr)
                    for attr in self.model.meta.fields_mapping.keys()
                    if not attr in columns and not attr.startswith("_")
                },
            }
            for result in raw_result
        ]

    async def filter_and_list(
        self,
        and_check: dict = None,
        or_check: dict = None,
        page: int = 1,
        per_page: int = 10,
        order_by: str = "id",
        sort_by: SortEnum = SortEnum.DESC,
        load_related: bool = False,
        total_count: int = None,
        select: str = None,
        object_only: bool = False,
        export_to_excel: bool = False,
    ) -> IFilterList | list[ModelType] | StreamingResponse:
        if and_check is None:
            and_check = {}
        query = self.query
        if or_check:
            query = query.or_(**or_check)
        if and_check:
            query = query.and_(**and_check)
        if not and_check or or_check:
            query = query.all()

        if load_related and self.get_related:
            query = query.prefetch_related(*self.get_related)
        if sort_by == SortEnum.ASC and order_by:
            query = query.order_by(
                *[
                    f"{col.strip()}"
                    for col in order_by.split(",")
                    if col in self.model._meta.fields
                ]
            )
        elif sort_by == SortEnum.DESC:
            query = query.order_by(
                *[
                    f"-{col.strip()}"
                    for col in order_by.split(",")
                    if col in self.model._meta.fields
                ]
            )
        else:
            query = query.order_by("-id")
        query = query.offset((page - 1) * per_page).limit(per_page)
        if select:
            query = query.values(
                *[
                    col.strip()
                    for col in select.split(",")
                    if col.strip() in self.model._meta.fields
                    and col.strip() not in self.get_related
                ]
            )
        raw_result = await query
        if object_only:
            return raw_result
        if load_related and raw_result and not select and not export_to_excel:
            raw_result = await self.to_dict(raw_result=raw_result)
        else:
            raw_result = [dict(data) for data in raw_result]
        if export_to_excel:
            return self.write_to_excel(models=raw_result, filename=self.model_name)
        if total_count is None:
            get_count = await self.get_count(
                or_check=or_check,
                and_check=and_check,
            )
            total_count = get_count.count if get_count else 0
        return IFilterList(
            data=raw_result,
            status=200,
            total_count=total_count,
        )

    async def delete_by_ids(self, object_ids: List[int], and_check: dict = None) -> int:
        if and_check is None:
            and_check = {}
        query = self.query
        if and_check:
            query.and_(**and_check)
        query = query.filter(id__in=object_ids)
        return await query.delete()

    async def delete_by_id(
        self, object_id: int, raise_error: bool = False
    ) -> ModelType:
        result = await self.query.filter(id=object_id).delete()
        if result <= 0:
            if raise_error:
                raise get_error_response(
                    f"{self.model_name} does not exist",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            else:
                return result
        return result

    async def get_by_ids(self, object_ids: List[uuid.UUID]) -> list[ModelType]:
        return await self.query.filter(id__in=object_ids).all()

    async def get(self, id: str, raise_error: bool = False) -> Optional[ModelType]:
        query = self.query.filter(id=id)
        obj = await query.first()
        if obj is not None:
            return obj
        if raise_error and not obj:
            raise get_error_response(
                detail=f"{self.model_name} is not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return obj

    async def get_all(self, limit: int = 10, offset: int = 0) -> List[ModelType]:
        return await self.query.all().offset(offset).limit(limit)

    async def filter_obj(
        self,
        get_first: bool = False,
        and_check: dict = None,
        or_check: dict = None,
        load_related: bool = False,
        raise_error: bool = False,
    ) -> List[ModelType] | ModelType:
        if and_check is None:
            and_check = {}
        query = self.query
        if load_related:
            query = query.prefetch_related(
                *self.get_related_backward,
                *self.get_related,
            )
        if get_first:
            result = await query.and_(**or_check, **and_check).first()
        else:
            result = await query.and_(**and_check).all()
        if not result and raise_error:
            raise get_error_response(
                f"{self.model_name} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return result

    async def get_count(
        self, and_check: dict = None, or_check: tuple | list | set = ()
    ) -> ICount:
        if and_check is None:
            and_check = {}
        query = self.query
        if or_check:
            query = query.filter(**or_check)
        if and_check:
            query = query.filter(**and_check)
        result = await query.all().count()
        return ICount(count=result)

    async def create(
        self,
        payload: dict | Struct,
        to_dict: bool = False,
    ) -> ModelType:
        data_dict = (
            msgspec.structs.asdict(payload) if isinstance(payload, Struct) else payload
        )

        instance = await self.model.create(**data_dict)
        return dict(instance) if to_dict else instance

    def generate_excel_content(self, payload: List[ModelType | dict | Struct]):
        data: list[dict] = []
        for model in payload:
            if isinstance(model, Struct) and model:
                data.append(msgspec.structs.asdict(model))
            elif isinstance(model, Model) and model:
                data.append(dict(model))
            else:
                data.append(model)
        wb = openpyxl.Workbook()
        ws = wb.active

        data = msgspec.json.encode(data)
        data = msgspec.json.decode(data)
        ws.title = self.model_name
        if len(data) > 0:
            ws.append(tuple(data[0].keys()))
        for model in data:
            ws.append(tuple(model.values()))
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        yield from output

    def write_to_excel(
        self, models: List[ModelType | dict | Struct], filename: str
    ) -> StreamingResponse:
        filename = f"{filename or self.model_name}.xlsx"
        return StreamingResponse(
            self.generate_excel_content(models),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    async def update(
        self, id: str, payload: Struct | dict, and_check: dict = None
    ) -> ModelType:
        query = self.query.filter(id=id)
        if and_check:
            query = query.and_(**and_check)
        instance = await query.first()
        item = (
            msgspec.structs.asdict(payload) if isinstance(payload, Struct) else payload
        )
        if not instance:
            raise get_error_response(
                f"{self.model_name} does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        for key, value in item.items():
            setattr(instance, key, value)
        await instance.save()
        return instance

    async def delete(self, id: str, and_check: dict = None) -> ModelType:
        if and_check is None:
            and_check = {}
        instance = await self.filter_obj(
            and_check=dict(id=id, **and_check),
            get_first=True,
            raise_error=True,
        )
        await instance.delete()
        return instance

    async def get_or_create(
        self,
        payload: Struct | dict,
        raise_error: bool = False,
        and_check: dict = None,
    ) -> ModelType:
        data_dict = (
            msgspec.structs.asdict(payload) if isinstance(payload, Struct) else payload
        )
        and_check = and_check or {}
        check_item = await self.query.filter(**and_check).first()
        if check_item and raise_error:
            raise get_error_response(
                f"{self.model_name} already exists",
                status_code=status.HTTP_409_CONFLICT,
            )
        elif not raise_error and check_item:
            return check_item
        check_item = await self.model.create(**data_dict)
        return check_item

    async def bulk_create(
        self,
        instances: list[dict],
    ) -> list[ModelType]:
        return await self.query.bulk_create(instances)

    async def bulk_update(self, instances: List[ModelType]) -> list[ModelType]:
        fields = self.model.meta.fields_mapping.keys()
        current_columns = set()
        if self.get_related:
            current_columns.update(self.get_related)
        if self.get_related_backward:
            current_columns.update(self.get_related_backward)
        if current_columns:
            for column in current_columns:
                if column in fields:
                    fields.remove(column)

        return await self.query.bulk_update(
            instances,
            fields=fields,
        )

    async def bulk_delete(self, objs: List[ModelType]) -> list[ModelType]:
        ids = [obj.id for obj in objs]
        result = await self.query.filter(id__in=ids).delete()
        return objs if result else None
