#  Copyright  2021 Alexis Lopez Zubieta
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
from pathlib import Path


class Executable:
    """Executable unit with its environment"""

    def __init__(self, path):
        self.path = Path(path)
        self.args = ["$@"]
        self.env = {}

    def __str__(self) -> str:
        return self.path

    def __eq__(self, o: object) -> bool:
        return (
            self.__class__ == o.__class__
            and self.path == o.path
            and self.args == o.args
        )


class BinaryExecutable(Executable):
    """Binary executable (an elf file)"""

    def __init__(self, path, arch):
        super().__init__(path)
        self.arch = arch

    def __eq__(self, o: object) -> bool:
        return (
            self.__class__ == o.__class__
            and self.path == o.path
            and self.arch == o.arch
        )

    def __str__(self) -> str:
        return super().__str__() + self.arch


class InterpretedExecutable(Executable):
    """Interpreted executable of any kind"""

    def __init__(self, path, shebang: [str]):
        super().__init__(path)
        self.shebang = shebang

    def __eq__(self, o: object) -> bool:
        return (
            self.__class__ == o.__class__
            and self.path == o.path
            and self.shebang == o.shebang
        )

    def __str__(self) -> str:
        return super().__str__() + self.shebang
