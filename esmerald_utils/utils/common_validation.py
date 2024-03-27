from typing import Annotated

import msgspec

Email = Annotated[
    str,
    msgspec.Meta(
        min_length=5,
        max_length=100,
        pattern="[^@]+@[^@]+\\.[^@]+",
    ),
]


UnixName = Annotated[
    str, msgspec.Meta(min_length=1, max_length=32, pattern="^[a-z_][a-z0-9_-]*$")
]
PhoneNumber = Annotated[
    str,
    msgspec.Meta(
        min_length=11,
        max_length=17,
        pattern=[
            "((^+)(234){1}[0–9]{10})|((^234)[0–9]{10})|((^0)(7|8|9){1}(0|1){1}[0–9]{8})"
        ],
    ),
]
Password = Annotated[
    str,
    #     Minimum eight characters, at least one uppercase letter, one lowercase letter, one number and one special character:
    msgspec.Meta(
        min_length=8,
        pattern=[
            "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        ],
    ),
]

StreetAddress = Annotated[str, msgspec.Meta(min_length=5)]
PostCode = Annotated[str, msgspec.Meta(min_length=5)]
