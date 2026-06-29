# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import asyncio
import logging

# Setup logging for backup module
backup_logger = logging.getLogger("BACKUP")

class AutoBackup:
    def __init__(self):
        self.source_client = ddw
        self.backup_client = backup_ddw
        self.db_name = DB_NAME
        self.owner_id = OWNER_ID
        self.backup_interval_hours = 24  # Backup every 24 hours
        self.max_backups = 3  # Keep last 3 days of backups
        
    async def get_backup_db_name(self, date_str=None):
        """Generate backup database name with date"""
        if not date_str:
            date_str = datetime.now().strftime("%d_%m_%Y")
        return f"{self.db_name}_{date_str}"
    
    async def check_last_backup(self):
        """Check when the last backup was created"""
        try:
            # List all databases to find backup databases
            db_list = await self.backup_client.list_database_names()
            backup_dbs = [db for db in db_list if db.startswith(f"{self.db_name}_")]
            
            if not backup_dbs:
                backup_logger.info("No previous backups found")
                return None
                
            # Sort backup databases by date (newest first)
            backup_dbs.sort(reverse=True)
            latest_backup = backup_dbs[0]
            
            # Extract date from backup name
            date_part = latest_backup.replace(f"{self.db_name}_", "")
            try:
                backup_date = datetime.strptime(date_part, "%d_%m_%Y")
                backup_logger.info(f"Latest backup found: {latest_backup} from {backup_date}")
                return backup_date
            except ValueError:
                backup_logger.error(f"Invalid backup date format: {date_part}")
                return None
                
        except Exception as e:
            backup_logger.error(f"Error checking last backup: {e}")
            return None
    
    async def create_backup(self):
        """Create a new backup of the database"""
        try:
            backup_logger.info("Starting database backup...")
            
            # Generate backup database name
            backup_db_name = await self.get_backup_db_name()
            backup_db = self.backup_client[backup_db_name]
            source_db = self.source_client[self.db_name]
            
            # Get all collections from source database
            collections = await source_db.list_collection_names()
            backup_logger.info(f"Found {len(collections)} collections to backup")
            
            total_docs = 0
            for collection_name in collections:
                source_collection = source_db[collection_name]
                backup_collection = backup_db[collection_name]
                
                # Get all documents from source collection
                documents = []
                async for doc in source_collection.find():
                    documents.append(doc)
                
                if documents:
                    # Insert documents into backup collection
                    await backup_collection.insert_many(documents)
                    total_docs += len(documents)
                    backup_logger.info(f"Backed up {len(documents)} documents from {collection_name}")
            
            backup_logger.info(f"Backup completed successfully! Total documents: {total_docs}")
            
            # Send notification to owner
            await self.send_backup_notification(backup_db_name, total_docs, len(collections))
            
            # Clean up old backups
            await self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            backup_logger.error(f"Error creating backup: {e}")
            await self.send_error_notification(str(e))
            return False
    
    async def cleanup_old_backups(self):
        """Remove backups older than max_backups days"""
        try:
            # List all backup databases
            db_list = await self.backup_client.list_database_names()
            backup_dbs = [db for db in db_list if db.startswith(f"{self.db_name}_")]
            
            if len(backup_dbs) <= self.max_backups:
                return
            
            # Sort by date (oldest first for deletion)
            backup_dates = []
            for db_name in backup_dbs:
                date_part = db_name.replace(f"{self.db_name}_", "")
                try:
                    backup_date = datetime.strptime(date_part, "%d_%m_%Y")
                    backup_dates.append((backup_date, db_name))
                except ValueError:
                    continue
            
            backup_dates.sort()  # Sort by date (oldest first)
            
            # Delete old backups
            while len(backup_dates) > self.max_backups:
                old_date, old_db_name = backup_dates.pop(0)
                await self.backup_client.drop_database(old_db_name)
                backup_logger.info(f"Deleted old backup: {old_db_name}")
                
        except Exception as e:
            backup_logger.error(f"Error cleaning up old backups: {e}")
    
    async def send_backup_notification(self, backup_name, total_docs, total_collections):
        """Send backup success notification to owner"""
        try:
            message = (
                f"✅ **Database Backup Completed**\n\n"
                f"📅 **Backup Name:** `{backup_name}`\n"
                f"📊 **Collections:** {total_collections}\n"
                f"📄 **Documents:** {total_docs}\n"
                f"⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                f"🔒 **Status:** Your data is safely backed up!"
            )
            
            await app.send_message(chat_id=self.owner_id, text=message)
            backup_logger.info("Backup notification sent to owner")
            
        except Exception as e:
            backup_logger.error(f"Error sending backup notification: {e}")
    
    async def send_error_notification(self, error_msg):
        """Send backup error notification to owner"""
        try:
            message = (
                f"❌ **Database Backup Failed**\n\n"
                f"🚨 **Error:** {error_msg}\n"
                f"⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                f"⚠️ Please check the backup system!"
            )
            
            await app.send_message(chat_id=self.owner_id, text=message)
            backup_logger.error("Backup error notification sent to owner")
            
        except Exception as e:
            backup_logger.error(f"Error sending error notification: {e}")
    
    async def should_create_backup(self):
        """Check if a new backup should be created"""
        last_backup = await self.check_last_backup()
        
        if not last_backup:
            backup_logger.info("No previous backup found, creating first backup")
            return True
        
        # Check if 24 hours have passed since last backup
        time_since_backup = datetime.now() - last_backup
        if time_since_backup >= timedelta(hours=self.backup_interval_hours):
            backup_logger.info(f"Time for new backup (last backup: {time_since_backup} ago)")
            return True
        
        backup_logger.info(f"Backup not needed yet (last backup: {time_since_backup} ago)")
        return False
    
    async def start_auto_backup(self):
        """Start the automatic backup system"""
        backup_logger.info("Auto backup system started")
        
        # Check if backup is needed on startup
        if await self.should_create_backup():
            await self.create_backup()
        
        # Schedule periodic backups
        while True:
            try:
                # Wait for 1 hour before checking again
                await asyncio.sleep(3600)  # 1 hour
                
                if await self.should_create_backup():
                    await self.create_backup()
                    
            except Exception as e:
                backup_logger.error(f"Error in auto backup loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

# Initialize backup system
backup_system = AutoBackup()

# Manual backup command for testing/emergency
@app.on_message(filters.command("backup"))
@require_power("VIP")
async def manual_backup(client: Client, message: Message):
    """Manual backup command for admins"""
    try:
        processing_msg = await message.reply_text("🔄 Creating manual backup...")
        
        success = await backup_system.create_backup()
        
        if success:
            await processing_msg.edit_text("✅ Manual backup completed successfully!")
        else:
            await processing_msg.edit_text("❌ Manual backup failed! Check logs for details.")
            
    except Exception as e:
        await message.reply_text(f"❌ Error creating manual backup: {str(e)}")

# Backup status command
@app.on_message(filters.command("backupstatus"))
@require_power("VIP")
async def backup_status(client: Client, message: Message):
    """Check backup system status"""
    try:
        last_backup = await backup_system.check_last_backup()
        
        if last_backup:
            time_since = datetime.now() - last_backup
            status_msg = (
                f"📊 **Backup System Status**\n\n"
                f"✅ **Last Backup:** {last_backup.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"⏰ **Time Since:** {time_since}\n"
                f"🔄 **Next Backup:** {'Soon' if time_since >= timedelta(hours=24) else 'In ' + str(timedelta(hours=24) - time_since)}\n"
                f"📁 **Max Backups:** {backup_system.max_backups} days\n"
                f"🔧 **Status:** Active"
            )
        else:
            status_msg = (
                f"📊 **Backup System Status**\n\n"
                f"❌ **Last Backup:** No backups found\n"
                f"🔄 **Next Backup:** Will create first backup soon\n"
                f"📁 **Max Backups:** {backup_system.max_backups} days\n"
                f"🔧 **Status:** Active"
            )
        
        await message.reply_text(status_msg)
        
    except Exception as e:
        await message.reply_text(f"❌ Error checking backup status: {str(e)}")

# List all backups command
@app.on_message(filters.command("listbackups"))
@require_power("VIP")
async def list_backups(client: Client, message: Message):
    """List all available backups"""
    try:
        db_list = await backup_system.backup_client.list_database_names()
        backup_dbs = [db for db in db_list if db.startswith(f"{backup_system.db_name}_")]
        
        if not backup_dbs:
            await message.reply_text("📁 No backups found.")
            return
        
        # Sort backups by date
        backup_info = []
        for db_name in backup_dbs:
            date_part = db_name.replace(f"{backup_system.db_name}_", "")
            try:
                backup_date = datetime.strptime(date_part, "%d_%m_%Y")
                backup_info.append((backup_date, db_name))
            except ValueError:
                continue
        
        backup_info.sort(reverse=True)  # Newest first
        
        backup_list = "📁 **Available Backups:**\n\n"
        for i, (backup_date, db_name) in enumerate(backup_info, 1):
            age = datetime.now() - backup_date
            backup_list += f"{i}. `{db_name}`\n   📅 {backup_date.strftime('%d/%m/%Y')}\n   ⏰ {age.days} days ago\n\n"
        
        await message.reply_text(backup_list)
        
    except Exception as e:
        await message.reply_text(f"❌ Error listing backups: {str(e)}")

# Start backup system command
@app.on_message(filters.command("startbackup"))
@require_power("OWNER")
async def start_backup_system_command(client: Client, message: Message):
    """Start the backup system manually (Owner only)"""
    try:
        processing_msg = await message.reply_text("🔄 Starting backup system...")
        
        # Start backup system in background
        asyncio.create_task(backup_system.start_auto_backup())
        
        await processing_msg.edit_text("✅ Backup system started successfully!")
        backup_logger.info("Backup system started manually by owner")
        
    except Exception as e:
        await message.reply_text(f"❌ Error starting backup system: {str(e)}")
        backup_logger.error(f"Error starting backup system: {e}")
