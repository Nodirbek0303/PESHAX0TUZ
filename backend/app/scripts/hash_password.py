from __future__ import annotations

import sys

from app.core.security import hash_password


def main() -> None:
    if len(sys.argv) < 2:
        print("Foydalanish: python -m app.scripts.hash_password \"YangiParol\"")
        raise SystemExit(1)
    password = sys.argv[1]
    print(hash_password(password))


if __name__ == "__main__":
    main()
