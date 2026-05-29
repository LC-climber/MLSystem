"""
Test Data Loading and Preprocessing

Simple tests to verify data loading and preprocessing modules work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loader import (
    load_train_data,
    load_test_data,
    get_data_summary,
    validate_data_integrity
)
from src.data.constants import ID_COL, TARGET_COL
from src.utils.logging import get_logger

logger = get_logger(__name__)


def test_data_loading():
    """Test basic data loading functionality."""
    logger.info("=" * 60)
    logger.info("Testing Data Loading")
    logger.info("=" * 60)

    try:
        # Load training data (first 100 rows for testing)
        logger.info("\n[1] Loading training data (first 100 rows)...")
        train_df = load_train_data(nrows=100)
        logger.info(f"✅ Loaded {len(train_df)} training samples")
        logger.info(f"   Columns: {list(train_df.columns)}")

        # Validate data integrity
        logger.info("\n[2] Validating data integrity...")
        validate_data_integrity(train_df, is_train=True)
        logger.info("✅ Data integrity check passed")

        # Get data summary
        logger.info("\n[3] Getting data summary...")
        summary = get_data_summary(train_df)
        logger.info(f"✅ Data summary:")
        logger.info(f"   Rows: {summary['n_rows']}")
        logger.info(f"   Columns: {summary['n_cols']}")
        logger.info(f"   Target distribution: {summary.get('target_distribution', 'N/A')}")

        # Check for missing values
        missing_cols = [
            col for col, rate in summary['missing_rates'].items()
            if rate > 0
        ]
        if missing_cols:
            logger.info(f"\n[4] Columns with missing values: {len(missing_cols)}")
            for col in missing_cols[:5]:  # Show first 5
                rate = summary['missing_rates'][col]
                logger.info(f"   {col}: {rate*100:.1f}%")
        else:
            logger.info("\n[4] No missing values found")

        logger.info("\n" + "=" * 60)
        logger.info("✅ All data loading tests passed!")
        logger.info("=" * 60)

        return True

    except FileNotFoundError as e:
        logger.error(f"\n❌ Data files not found: {e}")
        logger.error("Please download the data first:")
        logger.error("  bash scripts/fetch_data.sh")
        return False

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_data_loading()
    sys.exit(0 if success else 1)
