"""Seed de cuentas reales de estudiantes desde los registros de matricula del
IESTP RFA (ATI-V-M.xlsx = turno manana, ATI-V-N.xlsx = turno noche).

Crea una cuenta con role 'student' por cada matriculado en la unidad didactica
"Aplicaciones Moviles". Idempotente: omite los emails ya existentes. Emite un CSV
de credenciales para repartir a los estudiantes.

Estas son cuentas REALES de estudiantes reales. No son datos demo. La actividad
demo (progreso/quiz/chat) se genera aparte y queda rotulada como tal.

Uso (desde backend/):
    python scripts/seed_students.py --dry-run         # solo parsea + CSV, sin BD
    python scripts/seed_students.py                   # inserta en settings.DATABASE_URL
    python scripts/seed_students.py --password "Iestp2026!" --domain iestprfa.edu.pe
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import glob
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DOMAIN = "iestprfa.edu.pe"
DEFAULT_PASSWORD = "Iestp2026!"
APPS_MOVILES_COL = 11  # 0-indexed: primera columna de unidad didactica (1 = Aplicaciones Moviles)
PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "do"}
# Nombres sin coma con apellido compuesto que la heuristica no puede inferir.
# Clave = nombre crudo en mayusculas con espacios colapsados.
NO_COMMA_OVERRIDE = {
    "FLORES DE LA CRUZ PEDRO ALEJANDRO": ("FLORES DE LA CRUZ", "PEDRO ALEJANDRO"),
}


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def title_es(text: str) -> str:
    """Title-case respetando particulas (de, la, los...)."""
    words = text.lower().split()
    out = []
    for i, w in enumerate(words):
        out.append(w if (i > 0 and w in PARTICLES) else w.capitalize())
    return " ".join(out)


def parse_name(raw: str) -> tuple[str, str, str]:
    """Devuelve (nombre_natural, primer_nombre, primer_apellido) desde 'APELLIDOS, NOMBRES'."""
    raw = " ".join(str(raw).split())  # colapsa espacios y saltos de linea
    if raw.upper() in NO_COMMA_OVERRIDE:
        apellidos, nombres = NO_COMMA_OVERRIDE[raw.upper()]
    elif "," in raw:
        apellidos, nombres = [p.strip() for p in raw.split(",", 1)]
    else:
        # sin coma: asumimos 2 primeros tokens = apellidos, resto = nombres
        toks = raw.split()
        if len(toks) >= 3:
            apellidos, nombres = " ".join(toks[:2]), " ".join(toks[2:])
        elif len(toks) == 2:
            apellidos, nombres = toks[0], toks[1]
        else:
            apellidos, nombres = raw, ""
    first_name = nombres.split()[0] if nombres.split() else "estudiante"
    first_surname = apellidos.split()[0] if apellidos.split() else "rfa"
    full_natural = title_es(f"{nombres} {apellidos}".strip())
    return full_natural, first_name, first_surname


def email_for(first_name: str, first_surname: str, domain: str, used: set[str]) -> str:
    base = f"{strip_accents(first_name).lower()}.{strip_accents(first_surname).lower()}"
    base = "".join(ch for ch in base if ch.isalnum() or ch == ".")
    email = f"{base}@{domain}"
    n = 1
    while email in used:
        n += 1
        email = f"{base}{n}@{domain}"
    used.add(email)
    return email


def load_from_csv(path: str) -> list[dict]:
    """Carga estudiantes ya parseados desde el CSV de credenciales (sin openpyxl)."""
    students: list[dict] = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            students.append({
                "section": r.get("seccion", "?"),
                "dni": r.get("dni", ""),
                "raw_name": r.get("nombre", ""),
                "full_name": r["nombre"],
                "email": r["email"],
                "password": r.get("password") or None,
            })
    return students


def extract_students(files: list[str], domain: str) -> list[dict]:
    import openpyxl  # lazy: solo necesario al parsear xlsx (no en modo --from-csv)

    students: list[dict] = []
    used_emails: set[str] = set()
    for f in files:
        stem = Path(f).stem.upper()
        section = "manana" if stem.endswith("-M") else ("noche" if stem.endswith("-N") else "?")
        ws = openpyxl.load_workbook(f, data_only=True).active
        for row in ws.iter_rows(values_only=True):
            if not row or len(row) < 12:
                continue
            num, dni, name = row[0], row[1], row[2]
            if not isinstance(num, int):          # filas de cabecera/totales
                continue
            if name is None or not str(name).strip():
                continue
            if str(row[APPS_MOVILES_COL]).strip().upper() != "X":  # solo Aplicaciones Moviles
                continue
            dni_s = str(int(dni)) if isinstance(dni, (int, float)) else str(dni).strip()
            full_natural, fn, fs = parse_name(name)
            students.append({
                "section": section,
                "dni": dni_s,
                "raw_name": " ".join(str(name).split()),
                "full_name": full_natural,
                "email": email_for(fn, fs, domain, used_emails),
            })
    return students


def write_csv(students: list[dict], password: str, csv_path: str) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["seccion", "dni", "nombre", "email", "password"])
        for s in students:
            w.writerow([s["section"], s["dni"], s["full_name"], s["email"], password])


async def insert_students(students: list[dict], password: str) -> None:
    sys.path.insert(0, str(BACKEND_DIR))  # permite `import app...` desde scripts/
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.user import User
    from app.utils.security import hash_password

    print(f"BD destino: {settings.DATABASE_URL.split('@')[-1]}")
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    hash_cache: dict[str, str] = {}  # cachea por password (bcrypt es caro)

    def get_hash(pw: str) -> str:
        if pw not in hash_cache:
            hash_cache[pw] = hash_password(pw)
        return hash_cache[pw]

    created = skipped = 0
    async with Session() as db:
        for s in students:
            if await db.scalar(select(User).where(User.email == s["email"])):
                skipped += 1
                continue
            db.add(User(
                email=s["email"],
                full_name=s["full_name"],
                hashed_password=get_hash(s.get("password") or password),
                role="student",
                is_active=True,
            ))
            created += 1
        await db.commit()
    await engine.dispose()
    print(f"Creados: {created} | Omitidos (ya existian): {skipped}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Crea cuentas de estudiantes desde los xlsx de matricula.")
    ap.add_argument("--password", default=DEFAULT_PASSWORD, help="password compartido inicial")
    ap.add_argument("--domain", default=DEFAULT_DOMAIN, help="dominio de email institucional")
    ap.add_argument("--files", nargs="*", default=None, help="rutas xlsx (def: ATI-V-*.xlsx en raiz)")
    ap.add_argument("--csv", default=str(REPO_ROOT / "students_credentials.csv"))
    ap.add_argument("--from-csv", default=None, help="inserta desde un CSV ya generado (sin openpyxl)")
    ap.add_argument("--dry-run", action="store_true", help="parsea y emite CSV sin tocar la BD")
    args = ap.parse_args()

    if args.from_csv:
        students = load_from_csv(args.from_csv)
        print(f"Cargados desde CSV: {len(students)} estudiantes ({args.from_csv})")
    else:
        files = args.files or sorted(glob.glob(str(REPO_ROOT / "ATI-V-*.xlsx")))
        if not files:
            print("No se hallaron archivos ATI-V-*.xlsx en", REPO_ROOT)
            sys.exit(1)
        students = extract_students(files, args.domain)
        print(f"Matriculados en Aplicaciones Moviles: {len(students)}\n")
        for s in students:
            print(f"  [{s['section'][:6]:6s}] {s['full_name'][:36]:36s} {s['email']}")
        write_csv(students, args.password, args.csv)
        print(f"\nCredenciales -> {args.csv}  (password inicial: {args.password})")

    if args.dry_run:
        print("DRY-RUN: sin escritura en BD.")
        return
    asyncio.run(insert_students(students, args.password))


if __name__ == "__main__":
    main()
