class Console:
    """
    Reusable console renderer for Easy Data Fix.
    """

    WIDTH = 70

    @classmethod
    def divider(cls, character: str = "=") -> None:
        print(character * cls.WIDTH)

    @classmethod
    def title(cls, text: str) -> None:
        cls.divider()
        print(text.center(cls.WIDTH))
        cls.divider()

    @classmethod
    def section(cls, text: str) -> None:
        print()
        print(text)
        cls.divider("-")

    @staticmethod
    def key_value(key: str, value, indent: int = 0) -> None:
        padding = " " * indent
        print(f"{padding}{key:<15}: {value}")

    @staticmethod
    def recommendation(index: int, title: str) -> None:
        print(f"{index}. {title}")

    @staticmethod
    def blank() -> None:
        print()
