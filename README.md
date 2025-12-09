# Telegram Video Uploader Bot

A simple Telegram bot that automatically uploads videos from a specified directory and tracks which files have been uploaded with their Telegram links.

## Features

- 📹 Automatically scans a directory for video files
- ✅ Tracks uploaded videos in a JSON file
- 🔗 Saves Telegram message links for each uploaded video
- 🔄 Resumes from where it left off (only uploads new/unuploaded videos)
- 📊 Supports multiple video formats (mp4, avi, mkv, mov, flv, wmv, webm, m4v)
- 📝 Detailed logging of upload progress

## Setup

### 1. Install Dependencies

This project uses `uv` for dependency management:

```powershell
uv sync
```

Or if you prefer pip:
```powershell
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### 3. Get Your Chat ID

**Option A: Personal Chat**
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":...}` in the response

**Option B: Channel/Group**
1. Add your bot to a channel or group as an admin
2. Send a message in that channel/group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the chat ID (for channels, it will be like `-100xxxxxxxxxx`)

### 4. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and fill in your details:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   CHAT_ID=your_chat_id_here
   VIDEO_PATH=C:\path\to\your\videos
   ```

## Usage

### Upload Videos

Simply run the bot to start uploading unuploaded videos:

```powershell
uv run main.py
```

Or:
```powershell
python main.py
```

The bot will:
1. Scan the specified video directory
2. Check which files haven't been uploaded yet
3. Upload each video to Telegram
4. Save the upload link in `tracking.json`
5. Continue until all videos are uploaded

### Tracking File

The bot creates a `tracking.json` file that stores:
- File paths of uploaded videos
- Telegram message links
- Upload timestamps

Example `tracking.json`:
```json
{
  "uploaded": {
    "C:\\Videos\\video1.mp4": {
      "link": "https://t.me/c/1234567890/123",
      "uploaded_at": "2025-12-10T10:30:00.123456"
    },
    "C:\\Videos\\video2.mp4": {
      "link": "https://t.me/c/1234567890/124",
      "uploaded_at": "2025-12-10T10:32:15.654321"
    }
  }
```
fileuploaderbot/
├── main.py                # Main bot entry point
├── tracking_manager.py    # Tracking file management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
├── tracking.json         # Upload tracking file (auto-generated)
└── README.md             # This file
``` .env                   # Environment variables (create from .env.example)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
├── tracking.json         # Upload tracking file (auto-generated)
└── README.md             # This file
```

## Supported Video Formats

- `.mp4` - MPEG-4 Video
- `.avi` - Audio Video Interleave
- `.mkv` - Matroska Video
- `.mov` - QuickTime Movie
- `.flv` - Flash Video
- `.wmv` - Windows Media Video
- `.webm` - WebM Video
- `.m4v` - MPEG-4 Video

## Error Handling

- The bot logs all upload attempts
- Failed uploads are skipped and logged
- Successfully uploaded files are immediately marked in tracking file
- You can re-run the bot safely - it will only upload new files

## Tips

- **Large files**: Telegram has file size limits (2GB for bots)
- **Rate limits**: The bot includes a 2-second delay between uploads
- **Network issues**: If upload fails, just re-run the bot - it will resume
- **Multiple folders**: To upload from multiple folders, run the bot separately for each

## Troubleshooting

### Bot doesn't send messages
- Verify your `BOT_TOKEN` is correct
- Make sure the bot is not blocked
- For channels/groups, ensure the bot has admin permissions

### Chat ID issues
- For channels, the ID should start with `-100`
- For personal chats, it's usually a positive number
- For groups, it's a negative number

### Videos not found
- Check the `VIDEO_PATH` is correct
- Use absolute paths (e.g., `C:\Users\...\Videos`)
- Ensure the directory exists and contains video files

## License

MIT License - Feel free to use and modify as needed.
