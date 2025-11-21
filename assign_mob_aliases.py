#!/usr/bin/env python3
"""
Assign Mob Aliases to All CESAR Agents
Assigns permanent mob-style names from classic mafia films
"""

import os
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# Mob alias pool from classic mafia films
MOB_ALIASES = [
    # The Sopranos
    "Paulie Gualtieri",
    "Christopher Moltisanti",
    "Silvio Dante",
    "Bobby Baccalieri",
    "Vito Spatafore",
    "Ralph Cifaretto",
    "Richie Aprile",
    "Furio Giunta",

    # Goodfellas
    "Jimmy Conway",
    "Tommy DeVito",
    "Frankie Carbone",
    "Billy Batts",
    "Tuddy Cicero",

    # Casino
    "Nicky Santoro",
    "Ace Rothstein",
    "Ginger McKenna",
    "Frankie Marino",

    # The Godfather
    "Luca Brasi",
    "Pete Clemenza",
    "Sal Tessio",
    "Rocco Lampone",
    "Al Neri",
    "Moe Greene",
    "Johnny Fontane",

    # Donnie Brasco
    "Lefty Ruggiero",
    "Sonny Black",
    "Nicky Santangelo",

    # The Irishman
    "Frank Sheeran",
    "Russell Bufalino",
    "Angelo Bruno",

    # Boardwalk Empire
    "Nucky Thompson",
    "Jimmy Darmody",
    "Richard Harrow",
    "Al Capone",
    "Lucky Luciano",
    "Meyer Lansky",
    "Arnold Rothstein",

    # A Bronx Tale
    "Sonny LoSpecchio",
    "Calogero Anello",

    # Mean Streets
    "Johnny Boy",
    "Charlie Cappa",

    # The Untouchables
    "Al Capone",
    "Frank Nitti",
    "Malone",

    # Carlito's Way
    "Carlito Brigante",
    "David Kleinfeld",

    # Gotti
    "Sammy Gravano",
    "Neil Dellacroce",

    # Others
    "Bugsy Siegel",
    "Frank Costello",
    "Vito Genovese",
    "Carlo Gambino",
    "Joe Masseria",
    "Salvatore Maranzano",
    "Tommy Lucchese",
    "Joe Profaci",
    "Joe Bonanno",
    "Vincent Gigante",
    "Carmine Persico",
    "Paul Castellano",
]


def assign_aliases():
    """Assign mob aliases to all agents"""

    with psycopg.connect(**DB_CONFIG) as conn:
        cur = conn.cursor(row_factory=dict_row)

        # Get all agents
        cur.execute("""
            SELECT id, agent_id, name, type, metadata
            FROM agents
            ORDER BY created_at
        """)
        agents = cur.fetchall()

        print(f"🎭 Assigning mob aliases to {len(agents)} agents")
        print("=" * 80)

        for i, agent in enumerate(agents):
            # Skip CESAR (central_orchestrator gets special treatment)
            if agent['agent_id'] == 'central_orchestrator':
                mob_alias = "CESAR Sheppardini"
                specialization = "Boss - Primary Orchestrator"
            else:
                # Assign mob alias from pool
                mob_alias = MOB_ALIASES[i % len(MOB_ALIASES)]

                # Determine specialization from agent type
                specialization_map = {
                    'orchestrator': 'Multi-Agent Coordination',
                    'data': 'Data Collection & Processing',
                    'analysis': 'Analysis & Intelligence',
                    'prediction': 'Forecasting & Prediction',
                    'optimization': 'Optimization & Strategy',
                    'transformer': 'Workflow Transformation',
                    'generator': 'Content Generation',
                    'validation': 'Compliance & Validation',
                    'search': 'Information Retrieval',
                    'communication': 'External Communication',
                }
                specialization = specialization_map.get(agent['type'], agent['type'].title())

            # Update metadata with mob alias and specialization
            metadata = agent['metadata'] or {}
            metadata['mob_alias'] = mob_alias
            metadata['specialization'] = specialization
            metadata['voice_mode'] = 'third_person'
            metadata['hierarchy_role'] = 'boss' if agent['agent_id'] == 'central_orchestrator' else 'specialist'

            # Update agent
            cur.execute("""
                UPDATE agents
                SET metadata = %s
                WHERE id = %s
            """, (Jsonb(metadata), agent['id']))

            print(f"✅ {agent['name']:30} → {mob_alias:25} ({specialization})")

        conn.commit()
        print("\n" + "=" * 80)
        print(f"🎉 Successfully assigned mob aliases to all {len(agents)} agents!")


if __name__ == "__main__":
    assign_aliases()
