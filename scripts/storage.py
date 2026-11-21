import os
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import NamedTuple

import psycopg
from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DATABASE_DIR = Path(__file__).resolve().parents[1] / "database"
DATABASE_ERRORS = (psycopg.Error, PyMongoError, DriverError, Neo4jError)


class Stores(NamedTuple):
    postgres: object
    mongo: object
    graph: object


@contextmanager
def connect_postgres():
    with psycopg.connect(
        host="postgres", dbname="soundgraph", user="soundgraph",
        password=os.environ["POSTGRES_PASSWORD"], connect_timeout=4, autocommit=True,
        options="-c statement_timeout=5000 -c lock_timeout=3000",
    ) as connection:
        yield connection


def create_mongo_client():
    return MongoClient(
        "mongo", username="soundgraph", authSource="admin",
        password=os.environ["MONGO_INITDB_ROOT_PASSWORD"],
        serverSelectionTimeoutMS=3500, timeoutMS=4000,
    )


def create_graph_driver():
    return GraphDatabase.driver(
        "bolt://neo4j:7687", auth=("neo4j", os.environ["NEO4J_PASSWORD"]),
        connection_timeout=3, connection_acquisition_timeout=5, max_transaction_retry_time=1,
        telemetry_disabled=True,
    )


@contextmanager
def open_stores():
    with ExitStack() as stack:
        pg = stack.enter_context(connect_postgres())
        client = stack.enter_context(create_mongo_client())
        graph = stack.enter_context(create_graph_driver())
        client.admin.command("ping")
        graph.verify_connectivity()
        yield Stores(pg, client.soundgraph, graph)
