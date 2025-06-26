"""
Script to add the analysis column to the match table.
This script adds the analysis field that was added to the MatchBase model.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from the app
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_analysis_column():
    """Add the analysis column to the match table."""
    
    try:
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # First check if the column already exists
                check_column_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match' AND column_name = 'analysis';
                """
                
                result = connection.execute(text(check_column_sql))
                existing_column = result.fetchone()
                
                if existing_column:
                    logger.info("Analysis column already exists in match table. Skipping...")
                    return
                
                logger.info("Adding analysis column to match table...")
                
                # SQL statement to add the analysis column
                alter_table_sql = """
                ALTER TABLE match 
                ADD COLUMN analysis TEXT;
                """
                
                # Execute the ALTER TABLE statement
                connection.execute(text(alter_table_sql))
                
                logger.info("Successfully added analysis column to match table")
                
                # Verify the column was added
                verify_sql = """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'match' AND column_name = 'analysis';
                """
                
                result = connection.execute(text(verify_sql))
                column_info = result.fetchone()
                
                if column_info:
                    logger.info(f"Column verification successful: {column_info}")
                else:
                    logger.warning("Column verification failed - column not found")
                    
    except Exception as e:
        logger.error(f"Error adding analysis column: {e}")
        raise


def main():
    """Main function to run the migration."""
    try:
        logger.info("Starting migration to add analysis column...")
        add_analysis_column()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 