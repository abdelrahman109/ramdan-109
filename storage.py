import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('DB_PATH', str(BASE_DIR / 'instance' / 'tickets.db')))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {row[1] for row in conn.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in cols:
        conn.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')


def init_db() -> None:
    with db_cursor() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id TEXT,
                chat_id TEXT,
                booker_name TEXT,
                full_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                ticket_type TEXT NOT NULL,
                amount_egp INTEGER NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'pending',
                ticket_code TEXT NOT NULL UNIQUE,
                qr_secret TEXT NOT NULL UNIQUE,
                created_at TEXT,
                paid_at TEXT,
                used_at TEXT,
                is_used INTEGER NOT NULL DEFAULT 0,
                instapay_ref TEXT,
                notes TEXT,
                payment_proof_path TEXT,
                payment_proof_uploaded_at TEXT
            );
            """
        )
        _ensure_column(conn, 'tickets', 'booker_name', 'booker_name TEXT')
        _ensure_column(conn, 'tickets', 'instapay_ref', 'instapay_ref TEXT')
        _ensure_column(conn, 'tickets', 'notes', 'notes TEXT')
        _ensure_column(conn, 'tickets', 'payment_proof_path', 'payment_proof_path TEXT')
        _ensure_column(conn, 'tickets', 'payment_proof_uploaded_at', 'payment_proof_uploaded_at TEXT')


def insert_ticket(ticket: Dict[str, object]) -> int:
    with db_cursor() as conn:
        cur = conn.execute(
            '''
            INSERT INTO tickets (
                telegram_user_id, chat_id, booker_name, full_name, phone, email,
                ticket_type, amount_egp, payment_method, payment_status,
                ticket_code, qr_secret, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                ticket.get('telegram_user_id'),
                ticket.get('chat_id'),
                ticket.get('booker_name'),
                ticket['full_name'],
                ticket.get('phone'),
                ticket.get('email'),
                ticket['ticket_type'],
                ticket['amount_egp'],
                ticket['payment_method'],
                ticket['payment_status'],
                ticket['ticket_code'],
                ticket['qr_secret'],
                ticket.get('created_at'),
                ticket.get('notes', ''),
            ),
        )
        return int(cur.lastrowid)


def get_ticket_by_code(ticket_code: str):
    with db_cursor() as conn:
        return conn.execute('SELECT * FROM tickets WHERE ticket_code = ?', (ticket_code,)).fetchone()


def get_ticket_by_secret(secret: str):
    with db_cursor() as conn:
        return conn.execute('SELECT * FROM tickets WHERE qr_secret = ?', (secret,)).fetchone()


def get_ticket_by_id(ticket_id: int):
    with db_cursor() as conn:
        return conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()


def latest_tickets(limit: int = 200) -> List[sqlite3.Row]:
    with db_cursor() as conn:
        return conn.execute('SELECT * FROM tickets ORDER BY id DESC LIMIT ?', (limit,)).fetchall()


def sold_count() -> int:
    with db_cursor() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE payment_status = 'paid'").fetchone()
        return int(row['c'])


def used_count() -> int:
    with db_cursor() as conn:
        row = conn.execute('SELECT COUNT(*) AS c FROM tickets WHERE is_used = 1').fetchone()
        return int(row['c'])


def pending_count() -> int:
    with db_cursor() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE payment_status = 'pending'").fetchone()
        return int(row['c'])


def update_payment(ticket_code: str, status: str, paid_at: Optional[str] = None, instapay_ref: Optional[str] = None) -> None:
    with db_cursor() as conn:
        conn.execute(
            '''
            UPDATE tickets
            SET payment_status = ?,
                paid_at = COALESCE(?, paid_at),
                instapay_ref = COALESCE(?, instapay_ref)
            WHERE ticket_code = ?
            ''',
            (status, paid_at, instapay_ref, ticket_code),
        )


def mark_used(secret: str, used_at: str) -> bool:
    with db_cursor() as conn:
        row = conn.execute('SELECT id, is_used, payment_status FROM tickets WHERE qr_secret = ?', (secret,)).fetchone()
        if not row or row['is_used'] or row['payment_status'] != 'paid':
            return False
        conn.execute('UPDATE tickets SET is_used = 1, used_at = ? WHERE id = ?', (used_at, row['id']))
        return True


def set_instapay_ref(ticket_code: str, ref: str) -> None:
    with db_cursor() as conn:
        conn.execute('UPDATE tickets SET instapay_ref = ? WHERE ticket_code = ?', (ref, ticket_code))


def set_payment_proof(ticket_code: str, proof_path: str, uploaded_at: str) -> None:
    with db_cursor() as conn:
        conn.execute(
            'UPDATE tickets SET payment_proof_path = ?, payment_proof_uploaded_at = ? WHERE ticket_code = ?',
            (proof_path, uploaded_at, ticket_code),
        )


def get_ticket_by_user(user_id: str) -> List[sqlite3.Row]:
    with db_cursor() as conn:
        return conn.execute('SELECT * FROM tickets WHERE telegram_user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
