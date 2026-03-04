from sql_dump_query_engine import SQLDumpQueryEngine


def test_engine_import_and_instantiation() -> None:
    engine = SQLDumpQueryEngine()
    assert engine is not None
