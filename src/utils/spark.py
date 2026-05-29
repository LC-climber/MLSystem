"""
Spark Session Helper

Spark 3.5 runs on Java 8 / 11 / 17 but NOT Java 21. This machine's default
`java` is OpenJDK 21, so any SparkSession built without pinning JAVA_HOME dies on
startup. This helper pins JAVA_HOME to a Spark-compatible JDK *before* the JVM is
launched (Java 8 is preinstalled at /usr/lib/jvm/java-8-openjdk-amd64), then
returns a cached SparkSession configured from src.config.SPARK_CONFIG.

Override the JDK with the MLSYS_JAVA_HOME env var if you install Java 11/17 later
(preferred per 05_runbook_v2.md §1.5; Java 8 works too and needs no install).

It also pins PYSPARK_PYTHON to the driver's interpreter: without this, Spark
launches workers with the system `python3` (3.12 on Ubuntu 24.04) while the
conda driver is 3.11, and every job dies with PYTHON_VERSION_MISMATCH.

All P1 Spark code goes through get_spark_session() so the JVM is launched once
and reused across folds/models (a fresh SparkSession per fold would pay JVM
startup ~10x).
"""

import glob
import os
import sys
from typing import Optional

from src.config import SPARK_CONFIG
from src.utils.logging import get_logger

logger = get_logger(__name__)

_SPARK = None  # cached SparkSession (module-level singleton)


def _find_compatible_java() -> Optional[str]:
    """Locate a Spark-3.5-compatible JDK (8/11/17), preferring newer. None if none."""
    override = os.environ.get("MLSYS_JAVA_HOME")
    if override and os.path.isfile(os.path.join(override, "bin", "java")):
        return override
    # Prefer 17, then 11, then 8 — all Spark-3.5 compatible. Java 21 is excluded.
    patterns = [
        "/usr/lib/jvm/*17*",
        "/usr/lib/jvm/*-11-*", "/usr/lib/jvm/*1.11.0*",
        "/usr/lib/jvm/java-8-openjdk-*", "/usr/lib/jvm/*1.8.0*",
    ]
    for pat in patterns:
        for cand in sorted(glob.glob(pat)):
            if os.path.isfile(os.path.join(cand, "bin", "java")):
                return cand
    return None


def pin_java_home() -> str:
    """Set JAVA_HOME/PATH to a Spark-compatible JDK. Raises if none found."""
    java_home = _find_compatible_java()
    if java_home is None:
        raise RuntimeError(
            "No Spark-compatible JDK (8/11/17) found. Spark 3.5 does NOT support "
            "Java 21 (this machine's default `java`). Install one, e.g. "
            "`sudo apt install openjdk-17-jdk`, or point MLSYS_JAVA_HOME at a JDK."
        )
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = os.path.join(java_home, "bin") + os.pathsep + os.environ.get("PATH", "")
    return java_home


def pin_worker_python() -> str:
    """Force Spark workers + driver to use the current (conda) interpreter.

    Prevents PYTHON_VERSION_MISMATCH when the system python3 differs from the
    conda env running the driver.
    """
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    return sys.executable


# Pin at import so JAVA_HOME / PYSPARK_PYTHON are correct no matter how Spark is
# first touched.
pin_java_home()
pin_worker_python()


def get_spark_session(
    app_name: str = "mlsys-p1",
    master: str = "local[*]",
    enable_ui: bool = False,
):
    """Return the cached SparkSession, creating it (Java-pinned) on first call."""
    global _SPARK
    if _SPARK is not None:
        return _SPARK

    java_home = pin_java_home()
    pin_worker_python()
    os.makedirs(SPARK_CONFIG["spark.local.dir"], exist_ok=True)

    from pyspark.sql import SparkSession

    builder = SparkSession.builder.appName(app_name).master(master)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    builder = builder.config("spark.ui.enabled", "true" if enable_ui else "false")

    _SPARK = builder.getOrCreate()
    _SPARK.sparkContext.setLogLevel("ERROR")
    logger.info(
        "SparkSession up: spark=%s java=%s master=%s JAVA_HOME=%s",
        _SPARK.version,
        _SPARK._jvm.System.getProperty("java.version"),
        master,
        java_home,
    )
    return _SPARK


def stop_spark() -> None:
    """Stop the cached SparkSession (call once at the end of an experiment)."""
    global _SPARK
    if _SPARK is not None:
        _SPARK.stop()
        _SPARK = None
