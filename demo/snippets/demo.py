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


@dataclass(frozen=True)
class Bcd:
    @classmethod
    def f(cls):
        return cls


dummy = (True, False, None, str, float, sum)

abc = Abc(a=0, b=32.5, c="abc")
for i in range(len(argv)):
    print(f"{argv[0]} {len(argv)} {abc.d} {abc.d is float}")
