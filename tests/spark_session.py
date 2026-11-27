import pytest


@pytest.fixture(scope="session")
def spark():
    pyspark = pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession
    session = (SparkSession.builder.master("local[2]").appName("fabric-etl-validation")
               .config("spark.driver.host", "127.0.0.1").config("spark.driver.bindAddress", "127.0.0.1")
               .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "2")
               .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    yield session
    session.stop()
