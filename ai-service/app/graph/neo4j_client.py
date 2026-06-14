"""Neo4j driver singleton and schema/constraint setup."""

from app import config

_DRIVER = None


def get_neo4j_driver():
    global _DRIVER
    if _DRIVER is None:
        from neo4j import GraphDatabase

        _DRIVER = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
        )
    return _DRIVER


def ensure_schema() -> None:
    stmts = [
        "CREATE CONSTRAINT entity_name IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
        "FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
        "CREATE INDEX chunk_owner IF NOT EXISTS "
        "FOR (c:Chunk) ON (c.owner_id)",
    ]
    driver = get_neo4j_driver()
    with driver.session() as session:
        for stmt in stmts:
            session.run(stmt)
