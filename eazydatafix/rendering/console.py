class Console:
    """
    Reusable console renderer for EasyDataFix.
    """

    WIDTH = 72

    @classmethod
    def divider(cls, character: str = "=") -> None:
        print(character * cls.WIDTH)

    @classmethod
    def title(cls, text: str) -> None:
        cls.divider("=")
        print(text.center(cls.WIDTH))
        cls.divider("=")

    @classmethod
    def section(cls, text: str) -> None:
        print()
        print(text)
        cls.divider("-")

    @staticmethod
    def key_value(key: str, value, indent: int = 0) -> None:
        padding = " " * indent
        print(f"{padding}{key:<18}: {value}")

    @staticmethod
    def recommendation(index: int, title: str) -> None:
        print(f"{index}. {title}")

    @staticmethod
    def blank() -> None:
        print()

    @staticmethod
    def format_bytes(size: int) -> str:
        """
        Convert bytes into a human-readable string.
        """

        units = ["Bytes", "KB", "MB", "GB", "TB"]

        value = float(size)

        for unit in units:
            if value < 1024 or unit == units[-1]:
                if unit == "Bytes":
                    return f"{int(value)} {unit}"
                return f"{value:.2f} {unit}"
            value /= 1024

    @staticmethod
    def quality_status(score: float) -> str:
        """
        Return a friendly dataset quality status.
        """

        if score >= 95:
            return "Excellent ✅"

        if score >= 85:
            return "Good 👍"

        if score >= 70:
            return "Fair ⚠️"

        return "Needs Attention ❌"
