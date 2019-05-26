#!/usr/bin/python3

import sqlite3


def create_db(DB_FILE, TABLE):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                time text PRIMARY KEY,
                mcc integer,
                mnc integer,
                lac integer,
                cell_id integer,
                rxl integer,
                arfcn text,
                bsic text,
                lat float,
                lon float,
                satellites integer,
                GPS_quality text,
                altitude float,
                altitude_units text
            );""")
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f'failed to connect to db: {e}')