import random
import string
from uuid import uuid4
import slugify

# lsjkdj
def random_generator(size: int = 7, prefix: str = "") -> str:
    token = "".join(
        random.choices(
            string.ascii_uppercase + uuid4().hex.upper() + uuid4().hex.lower(),
            k=size,
        )
    )
    if prefix is None:
        return token
    return f"{prefix}{token}"


def slugify_generator(
    text: str,
    add_random: bool = False,
    size: int = 7,
    max_length: int | None = None,
):
    token = slugify.slugify(text=text)
    if add_random:
        return f"{token-{random_generator(size)}}"
    token = slugify.slugify(text=text)
    if max_length:
        return token[:max_length]
    return token
