from dataclasses import dataclass
from sys import argv


# A simple dataclass
@dataclass
class Abc[T]:
    a: int
    b: T
    c: str | None

    def __getattr__(self, name: str):
        return name


dummy = (True, False, None, str, float, sum)

abc = Abc(a=0, b=32.5, c="abc")
print(f"{argv[0]} {len(argv)} {abc.d}")
