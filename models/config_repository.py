import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional


class ConfigRepository:
    def __init__(self, db_path: str = "waveform_configs.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS config_profiles (
                    name TEXT PRIMARY KEY,
                    waveform TEXT NOT NULL,
                    frequency REAL NOT NULL,
                    amplitude REAL NOT NULL,
                    offset REAL NOT NULL,
                    phase REAL NOT NULL,
                    channel1 INTEGER NOT NULL,
                    channel2 INTEGER NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def save_profile(self, name: str, config: Dict) -> None:
        with self._lock, sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO config_profiles (
                    name, waveform, frequency, amplitude, offset, phase, channel1, channel2, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    waveform=excluded.waveform,
                    frequency=excluded.frequency,
                    amplitude=excluded.amplitude,
                    offset=excluded.offset,
                    phase=excluded.phase,
                    channel1=excluded.channel1,
                    channel2=excluded.channel2,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    name,
                    config["waveform"],
                    config["frequency"],
                    config["amplitude"],
                    config["offset"],
                    config["phase"],
                    int(bool(config["channels"].get(1, False))),
                    int(bool(config["channels"].get(2, False))),
                ),
            )
            connection.commit()

    def load_profile(self, name: str) -> Optional[Dict]:
        with self._lock, sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT name, waveform, frequency, amplitude, offset, phase, channel1, channel2, updated_at
                FROM config_profiles
                WHERE name = ?
                """,
                (name,),
            ).fetchone()

        if row is None:
            return None

        return {
            "name": row[0],
            "waveform": row[1],
            "frequency": row[2],
            "amplitude": row[3],
            "offset": row[4],
            "phase": row[5],
            "channels": {1: bool(row[6]), 2: bool(row[7])},
            "updated_at": row[8],
        }

    def list_profiles(self) -> List[Dict]:
        with self._lock, sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT name, waveform, frequency, amplitude, offset, phase, channel1, channel2, updated_at
                FROM config_profiles
                ORDER BY updated_at DESC, name ASC
                """
            ).fetchall()

        return [
            {
                "name": row[0],
                "waveform": row[1],
                "frequency": row[2],
                "amplitude": row[3],
                "offset": row[4],
                "phase": row[5],
                "channels": {1: bool(row[6]), 2: bool(row[7])},
                "updated_at": row[8],
            }
            for row in rows
        ]
