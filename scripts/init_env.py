import os
import secrets
from pathlib import Path


def write_env(target, keys):
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"{target.name} ya existe; no se sobrescribió.")
        return
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        for key in keys:
            stream.write(f"{key}={secrets.token_hex(24)}\n")
    print(f"{target.name} generado con credenciales locales.")


def main():
    root = Path(__file__).resolve().parents[1]
    write_env(root / ".env", ("POSTGRES_PASSWORD", "MONGO_INITDB_ROOT_PASSWORD", "NEO4J_PASSWORD"))
    write_env(root / ".env.demo", ("DEMO_CODE_ANA", "DEMO_CODE_SOFIA", "DEMO_CODE_NEW", "DEMO_CODE_EDITOR"))


if __name__ == "__main__":
    main()
