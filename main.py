import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from tracking_manager import TrackingManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
VIDEO_PATH = os.getenv('VIDEO_PATH')
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))  # Default 50MB
CONCURRENT_UPLOADS = int(os.getenv('CONCURRENT_UPLOADS', '1'))  # Concurrent uploads
UPLOAD_DELAY = float(os.getenv('UPLOAD_DELAY', '3.0'))  # Delay between uploads in seconds


class VideoUploaderBot:
    """Telegram bot for uploading videos."""
    
    def __init__(self, bot_token: str, chat_id: str, video_path: str, max_file_size_mb: int = 50):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.video_path = video_path
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.tracker = TrackingManager()
        self.semaphore = asyncio.Semaphore(CONCURRENT_UPLOADS)
        self.upload_delay = UPLOAD_DELAY
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    
    async def upload_video(self, file_path: str) -> str | None:
        """Upload a single video file to Telegram."""
        async with self.semaphore:
            try:
                # Check file size
                file_size_mb = self.get_file_size_mb(file_path)
                
                # Telegram limits: 2GB for bots, 50MB for send_video
                if file_size_mb > 2000:  # 2GB limit
                    logger.warning(f"⚠ Skipping {Path(file_path).name} - File too large ({file_size_mb:.1f}MB > 2000MB)")
                    self.tracker.mark_uploaded(file_path, f"SKIPPED: Too large ({file_size_mb:.1f}MB)")
                    return None
                
                # Use send_video for files <= 50MB, send_document for larger files
                use_video_method = file_size_mb <= self.max_file_size_mb
                method_name = "send_video" if use_video_method else "send_document"
                
                logger.info(f"Uploading: {Path(file_path).name} ({file_size_mb:.1f}MB) via {method_name}")
                
                with open(file_path, 'rb') as video_file:
                    if use_video_method:
                        message = await self.bot.send_video(
                            chat_id=self.chat_id,
                            video=video_file,
                            caption=f"📹 {Path(file_path).name}",
                            read_timeout=600,
                            write_timeout=600,
                            connect_timeout=60
                        )
                    else:
                        message = await self.bot.send_document(
                            chat_id=self.chat_id,
                            document=video_file,
                            caption=f"📹 {Path(file_path).name}",
                            read_timeout=600,
                            write_timeout=600,
                            connect_timeout=60
                        )
                
                # Get file link (using file_id as reference)
                file_link = f"https://t.me/c/{str(self.chat_id).replace('-100', '')}/{message.message_id}"
                
                logger.info(f"✓ Uploaded successfully: {Path(file_path).name}")
                
                # Add delay after successful upload to avoid flood control
                if self.upload_delay > 0:
                    await asyncio.sleep(self.upload_delay)
                
                return file_link
                
            except TelegramError as e:
                if "429" in str(e) or "flood" in str(e).lower() or "too many requests" in str(e).lower():
                    # Handle flood control - wait longer
                    logger.warning(f"⚠ Flood control hit! Waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return None
                if "413" in str(e) or "too large" in str(e).lower():
                    logger.error(f"✗ File too large for Telegram: {Path(file_path).name} ({file_size_mb:.1f}MB)")
                    self.tracker.mark_uploaded(file_path, f"ERROR: 413 Too Large ({file_size_mb:.1f}MB)")
                    return None
                logger.error(f"✗ Upload failed for {file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"✗ Unexpected error for {file_path}: {e}")
                raise
    
    async def process_uploads(self):
        """Process all unuploaded videos with concurrent uploads."""
        try:
            # Get list of unuploaded files
            unuploaded_files = self.tracker.get_unuploaded_files(self.video_path)
            
            if not unuploaded_files:
                logger.info("✓ All videos are already uploaded!")
                stats = self.tracker.get_stats()
                logger.info(f"Total uploaded files: {stats['total_uploaded']}")
                return
            
            # Sort by file size (smallest first for faster initial progress)
            unuploaded_files_with_size = [(f, self.get_file_size_mb(f)) for f in unuploaded_files]
            unuploaded_files_with_size.sort(key=lambda x: x[1])
            unuploaded_files = [f for f, _ in unuploaded_files_with_size]
            
            total_files = len(unuploaded_files)
            logger.info(f"Found {total_files} video(s) to upload")
            logger.info(f"Using {CONCURRENT_UPLOADS} concurrent uploads")
            logger.info(f"Max file size: {self.max_file_size_mb}MB\n")
            
            # Process in batches with concurrent uploads
            uploaded_count = 0
            failed_count = 0
            skipped_count = 0
            
            batch_size = CONCURRENT_UPLOADS * 5  # Process in batches
            for batch_start in range(0, total_files, batch_size):
                batch_files = unuploaded_files[batch_start:batch_start + batch_size]
                
                # Create upload tasks for this batch
                tasks = []
                for file_path in batch_files:
                    task = self.upload_and_track(file_path)
                    tasks.append(task)
                
                # Execute batch concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    elif result is None:
                        skipped_count += 1
                    else:
                        uploaded_count += 1
                
                # Progress update
                processed = min(batch_start + batch_size, total_files)
                logger.info(f"\n📊 Progress: {processed}/{total_files} processed | ✓ {uploaded_count} uploaded | ⚠ {skipped_count} skipped | ✗ {failed_count} failed\n")
            
            # Show final stats
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Upload session complete!")
            logger.info(f"Total processed: {total_files}")
            logger.info(f"Successfully uploaded: {uploaded_count}")
            logger.info(f"Skipped (too large): {skipped_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"{'='*60}\n")
            
        except FileNotFoundError as e:
            logger.error(f"Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during processing: {e}")
    
    async def upload_and_track(self, file_path: str) -> str | None:
        """Upload a video and track it."""
        try:
            file_link = await self.upload_video(file_path)
            if file_link:
                self.tracker.mark_uploaded(file_path, file_link)
                return file_link
            return None
        except Exception as e:
            logger.error(f"Failed to upload {Path(file_path).name}: {e}")
            return None
    
    async def get_stats(self):
        """Display upload statistics."""
        stats = self.tracker.get_stats()
        logger.info(f"\n=== Upload Statistics ===")
        logger.info(f"Total uploaded: {stats['total_uploaded']}")
        
        if stats['files']:
            logger.info(f"\nUploaded files:")
            for file_path in stats['files']:
                link = self.tracker.get_file_link(file_path)
                logger.info(f"  - {Path(file_path).name}: {link}")


def main():
    """Main entry point."""
    if not all([BOT_TOKEN, CHAT_ID, VIDEO_PATH]):
        logger.error("Missing required environment variables!")
        logger.error("Please set BOT_TOKEN, CHAT_ID, and VIDEO_PATH in your .env file")
        return
    
    # Type assertions for type checker
    assert BOT_TOKEN is not None
    assert CHAT_ID is not None
    assert VIDEO_PATH is not None
    
    logger.info("=== Telegram Video Uploader Bot ===\n")
    logger.info(f"Video path: {VIDEO_PATH}")
    logger.info(f"Chat ID: {CHAT_ID}")
    logger.info(f"Max file size: {MAX_FILE_SIZE_MB}MB")
    logger.info(f"Concurrent uploads: {CONCURRENT_UPLOADS}")
    logger.info(f"Upload delay: {UPLOAD_DELAY}s\n")
    
    bot = VideoUploaderBot(BOT_TOKEN, CHAT_ID, VIDEO_PATH, MAX_FILE_SIZE_MB)
    
    # Process uploads
    asyncio.run(bot.process_uploads())


if __name__ == "__main__":
    main()
