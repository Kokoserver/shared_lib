from msgspec import Struct


class BaseStruct(Struct):
    def to_dict(self, exclude: set[str] = None, exclude_none: bool = False):
        if exclude is None:
            exclude = set()

        fields = {
            f: getattr(self, f) for f in self.__struct_fields__ if f not in exclude
        }

        if exclude_none:
            fields = {f: v for f, v in fields.items() if v is not None}

        return fields
