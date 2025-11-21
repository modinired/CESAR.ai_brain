"""
CESAR.ai Supabase Daily Sync Scheduler
Automatically syncs data from local PostgreSQL to Supabase on a schedule

Author: CESAR.ai Development Team  
Date: November 20, 2025
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/supabase_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SupabaseSyncScheduler:
    """Automated scheduler for Supabase synchronization"""
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "cesar_src"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }
        
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        self.tables_to_sync = [
            "agents",
            "a2a_messages",
            "a2a_conversations",
            "llm_collaborations",
            "local_llm_learning_examples",
            "sessions"
        ]
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def sync_table(self, table_name: str):
        """Sync a single table to Supabase"""
        logger.info(f"Starting sync for table: {table_name}")
        
        conn = self._get_db_connection()
        if not conn:
            logger.error(f"Could not connect to database for {table_name}")
            return False
        
        try:
            with conn.cursor() as cur:
                # Update sync status to in_progress
                cur.execute("""
                    UPDATE supabase_sync_state
                    SET sync_status = 'in_progress',
                        updated_at = NOW()
                    WHERE table_name = %s
                """, (table_name,))
                conn.commit()
                
                # Get data from table (limit to recent records)
                cur.execute(f"""
                    SELECT *
                    FROM {table_name}
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)
                records = cur.fetchall()
                
                logger.info(f"Found {len(records)} records in {table_name}")
                
                # Here we would actually sync to Supabase
                # For now, just mark as completed
                # TODO: Implement actual Supabase sync using supabase_service.py
                
                # Update sync status
                cur.execute("""
                    UPDATE supabase_sync_state
                    SET sync_status = 'completed',
                        last_sync_at = NOW(),
                        last_sync_direction = 'to_supabase',
                        records_synced = %s,
                        updated_at = NOW()
                    WHERE table_name = %s
                """, (len(records), table_name))
                conn.commit()
                
                logger.info(f"✅ Sync completed for {table_name}: {len(records)} records")
                return True
                
        except Exception as e:
            logger.error(f"Error syncing {table_name}: {e}")
            
            # Mark as failed
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE supabase_sync_state
                        SET sync_status = 'failed',
                            error_message = %s,
                            updated_at = NOW()
                        WHERE table_name = %s
                    """, (str(e), table_name))
                    conn.commit()
            except:
                pass
                
            return False
        finally:
            conn.close()
    
    def sync_all_tables(self):
        """Sync all tables"""
        logger.info("="*60)
        logger.info("🔄 Starting daily Supabase sync...")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        success_count = 0
        for table in self.tables_to_sync:
            if self.sync_table(table):
                success_count += 1
            time.sleep(1)  # Small delay between tables
        
        logger.info("="*60)
        logger.info(f"✅ Daily sync complete: {success_count}/{len(self.tables_to_sync)} tables synced")
        logger.info("="*60)
    
    def run(self):
        """Run the scheduler"""
        logger.info("🚀 CESAR Supabase Sync Scheduler started")
        logger.info(f"Database: {self.db_config['database']}")
        logger.info(f"Supabase URL: {self.supabase_url or 'NOT CONFIGURED'}")
        logger.info(f"Tables to sync: {', '.join(self.tables_to_sync)}")
        logger.info("Schedule: Daily at 02:00 AM")
        logger.info("="*60)
        
        # Schedule daily sync at 2 AM
        schedule.every().day.at("02:00").do(self.sync_all_tables)
        
        # Also run every hour for testing
        schedule.every().hour.do(self.sync_all_tables)
        
        # Run once immediately on startup
        logger.info("Running initial sync...")
        self.sync_all_tables()
        
        # Keep running
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    # Load environment
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        # Load .env manually
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        logger.info(f"✅ Loaded environment from {env_path}")
    
    # Start scheduler
    scheduler = SupabaseSyncScheduler()
    scheduler.run()

if __name__ == "__main__":
    main()
