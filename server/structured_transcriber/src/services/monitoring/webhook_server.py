#!/usr/bin/env python3
"""
Google Drive Webhook Server (Modified for My Drive root)
Real-time file detection using Google Drive Push Notifications
Monitors My Drive root for audio files

Phase 15.1: Auto-renewal webhook channel support
"""

import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
from datetime import datetime, timedelta, timezone
import threading
from dotenv import load_dotenv
from filelock import FileLock, Timeout
import time
import asyncio

# Phase 10-3: Unified registry for duplicate detection
from src.utils.file_management import unified_registry as registry

# Load environment variables
load_dotenv()

# Constants from environment variables
# Phase 20: 統一スコープを使用
SCOPES_STR = os.getenv('GOOGLE_ALL_SCOPES', 'https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/calendar.readonly')
SCOPES = [s.strip() for s in SCOPES_STR.split(',')]
TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
PROCESSED_FILE = os.getenv('PROCESSED_FILE', '.processed_drive_files.txt')
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', 'downloads'))
PAGE_TOKEN_FILE = '.start_page_token.txt'
CHANNEL_FILE = '.channel_info.json'

# Lock directory for preventing duplicate processing
LOCK_DIR = Path('.processing_locks')
LOCK_DIR.mkdir(exist_ok=True)

# Webhook notification channel will expire after this duration
CHANNEL_EXPIRATION_HOURS = int(os.getenv('CHANNEL_EXPIRATION_HOURS', '24'))

# Auto-renewal settings
WEBHOOK_PUBLIC_URL = os.getenv('WEBHOOK_PUBLIC_URL', '')  # Set this in .env
ENABLE_AUTO_RENEWAL = os.getenv('ENABLE_WEBHOOK_AUTO_RENEWAL', 'true').lower() == 'true'
RENEWAL_CHECK_INTERVAL_HOURS = 6  # Check every 6 hours (24h expiry / 4 = safe margin)


def cleanup_old_locks():
    """Remove stale lock files on startup (handles abnormal termination cases)"""
    current_time = time.time()
    stale_threshold = 1800  # 30 minutes in seconds

    for lock_file in LOCK_DIR.glob('*.lock'):
        try:
            # Check if lock file is older than threshold
            if current_time - lock_file.stat().st_mtime > stale_threshold:
                print(f"[Cleanup] Removing stale lock: {lock_file.name}")
                lock_file.unlink(missing_ok=True)
        except Exception as e:
            print(f"[Warning] Failed to clean up {lock_file.name}: {e}")


def get_drive_service():
    """Get authenticated Google Drive service"""
    if not os.path.exists(TOKEN_PATH):
        raise Exception(f"Token not found. Please run drive_download.py first to authenticate.")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('drive', 'v3', credentials=creds)


def get_root_folder_id():
    """Return My Drive root folder ID"""
    return 'root'


def get_start_page_token(service):
    """Get or retrieve start page token for changes API"""
    if os.path.exists(PAGE_TOKEN_FILE):
        with open(PAGE_TOKEN_FILE, 'r') as f:
            return f.read().strip()

    # Get initial page token
    response = service.changes().getStartPageToken().execute()
    token = response.get('startPageToken')

    # Save it
    with open(PAGE_TOKEN_FILE, 'w') as f:
        f.write(token)

    return token


def save_page_token(token):
    """Save page token for next changes check"""
    with open(PAGE_TOKEN_FILE, 'w') as f:
        f.write(token)


def get_processed_files():
    """Read processed file IDs"""
    if not os.path.exists(PROCESSED_FILE):
        return set()

    with open(PROCESSED_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def mark_as_processed(file_id):
    """Mark file as processed (with duplicate check)"""
    processed = get_processed_files()
    if file_id not in processed:
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{file_id}\n")


def download_file(service, file_id, file_name):
    """Download file from Google Drive"""
    request = service.files().get_media(fileId=file_id)

    DOWNLOAD_DIR.mkdir(exist_ok=True)
    file_path = DOWNLOAD_DIR / file_name

    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    return file_path


def transcribe_file(audio_path):
    """Call structured_transcribe.py to transcribe (Gemini Audio API)"""
    cmd = [
        'python3.11',
        '-m',
        'src.services.transcription.structured_transcribe',
        str(audio_path)
    ]

    # Fix: Use log file instead of capturing output to avoid buffer deadlock
    # Large WAV files (329MB+) generate huge output that can fill subprocess.PIPE buffer
    log_file = f"logs/transcription_{Path(audio_path).stem}.log"
    print(f"[Debug] Starting transcription subprocess, logging to: {log_file}", flush=True)

    # Set timeout (default: 4 hours for very large files)
    timeout_seconds = int(os.getenv('TRANSCRIPTION_TIMEOUT_SECONDS', str(4 * 3600)))

    with open(log_file, 'w') as log_f:
        try:
            result = subprocess.run(
                cmd,
                stdout=log_f,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                env=os.environ.copy(),
                timeout=timeout_seconds
            )
        except subprocess.TimeoutExpired:
            error_msg = f"Transcription timed out after {timeout_seconds} seconds"
            print(f"[Error] {error_msg}", flush=True)
            raise Exception(error_msg)

    print(f"[Debug] Transcription subprocess completed", flush=True)
    print(f"[Debug] Exit code: {result.returncode}", flush=True)
    print(f"[Debug] Full log available at: {log_file}", flush=True)

    # Read last 50 lines of log for summary
    try:
        with open(log_file, 'r') as log_f:
            lines = log_f.readlines()
            summary_lines = lines[-50:] if len(lines) > 50 else lines
            print(f"[Debug] Last 50 lines of log:\n{''.join(summary_lines)}", flush=True)
    except Exception as e:
        print(f"[Warning] Could not read log summary: {e}", flush=True)

    if result.returncode != 0:
        error_msg = f"Transcription failed with exit code {result.returncode}\n"
        error_msg += f"Check full log at: {log_file}"
        print(f"[Error] {error_msg}", flush=True)
        raise Exception(error_msg)

    return f"Transcription completed successfully. Log: {log_file}"


def process_new_files(service, folder_id='root'):
    """Process new audio files in My Drive root"""
    print(f"[Debug] process_new_files called with folder_id={folder_id}", flush=True)
    processed_files = get_processed_files()
    print(f"[Debug] Loaded {len(processed_files)} processed files", flush=True)

    # Get all audio files in My Drive root
    # [Phase 15 Updated] Support both Voice Memos (via iCloud) and Plaud Note (via Google Drive)
    # My Drive root can have different parent IDs: 'root' or special ID like '0AC7SKrqIdnsGUk9PVA'
    # Strategy: Get all user-owned audio files, then filter to root level only
    query = f"mimeType contains 'audio/' and trashed=false and 'me' in owners"
    print(f"[Debug] Query: {query}", flush=True)
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, parents, createdTime)',
        orderBy='createdTime desc',
        pageSize=100
    ).execute()

    all_audio_files = results.get('files', [])
    print(f"[Debug] Found {len(all_audio_files)} total audio files owned by user", flush=True)

    # Filter to My Drive root level only (exclude files in subfolders)
    # My Drive root has parent name "My Drive" with special IDs
    audio_files = []
    for f in all_audio_files:
        parents = f.get('parents', [])
        if parents:
            # Check if parent is My Drive root (multiple possible IDs)
            parent_id = parents[0]
            # Get parent folder info to check if it's My Drive root
            try:
                parent = service.files().get(fileId=parent_id, fields='name, mimeType').execute()
                if parent.get('name') == 'My Drive':
                    audio_files.append(f)
                    print(f"[Debug]   Including: {f['name']} (parent: My Drive)", flush=True)
            except:
                # If we can't get parent info, assume it's in root
                audio_files.append(f)

    print(f"[Debug] Found {len(audio_files)} audio files in My Drive root", flush=True)
    new_files = [f for f in audio_files if f['id'] not in processed_files]
    print(f"[Debug] Found {len(new_files)} new files after filtering", flush=True)

    if not new_files:
        print("[Debug] No new files to process, returning", flush=True)
        return

    print(f"\n[Webhook] Found {len(new_files)} new file(s)", flush=True)

    for file_info in new_files:
        file_id = file_info['id']
        file_name = file_info['name']
        created_time = file_info.get('createdTime')  # ISO 8601形式 (例: "2025-10-16T01:54:11.881Z")

        # Lock file path for this specific file
        lock_path = LOCK_DIR / f"{file_id}.lock"
        lock = FileLock(lock_path, timeout=1)

        try:
            # Try to acquire lock (non-blocking with 0.1s timeout)
            with lock.acquire(timeout=0.1):
                print(f"\n[Processing] {file_name} (ID: {file_id})", flush=True)
                if created_time:
                    print(f"  Created: {created_time}", flush=True)

                try:
                    # Download
                    print(f"[1/4] Downloading...", flush=True)
                    audio_path = download_file(service, file_id, file_name)
                    print(f"  Saved to: {audio_path}", flush=True)

                    # [Phase 10-3 Updated] Extract user display name (filename without extension) and check for duplicates
                    # Now uses composite key (display_name + original_name + created_time) for duplicate detection
                    print(f"[2/4] Checking for duplicates...", flush=True)
                    user_display_name = Path(file_name).stem  # 拡張子なし
                    print(f"  User display name: {user_display_name}", flush=True)

                    if registry.is_processed(user_display_name, file_name, created_time):
                        existing = registry.get_by_display_name(user_display_name, file_name, created_time)
                        print(f"  ⚠️ DUPLICATE DETECTED - Already processed:", flush=True)
                        print(f"    Source: {existing.get('source')}", flush=True)
                        print(f"    Original: {existing.get('original_name')}", flush=True)
                        print(f"    Display name: {user_display_name}", flush=True)
                        print(f"    Processed at: {existing.get('processed_at')}", flush=True)
                        print(f"  ➡️ Skipping transcription, deleting files (local + cloud)", flush=True)

                        # Delete duplicate downloaded file
                        if audio_path.exists():
                            audio_path.unlink()
                            print(f"  ✅ Local file deleted", flush=True)

                        # [Phase 10-3.1] Delete duplicate file from Google Drive
                        try:
                            from src.utils.file_management.cloud_file_manager import (
                                delete_gdrive_file,
                                log_deletion,
                                get_file_size_mb
                            )

                            # Get file size for logging
                            file_size_mb = get_file_size_mb(service, file_id)

                            # Delete from Google Drive
                            delete_gdrive_file(service, file_id, file_name)
                            print(f"  ✅ Google Drive duplicate file deleted: {file_id}", flush=True)

                            # Log deletion event (with duplicate flag)
                            log_deletion(
                                file_info={
                                    'file_id': file_id,
                                    'file_name': file_name,
                                    'original_name': file_name,
                                    'file_size_mb': file_size_mb,
                                    'renamed_to': None
                                },
                                validation_results={
                                    'duplicate': True,
                                    'original_source': existing.get('source'),
                                    'original_processed_at': existing.get('processed_at')
                                },
                                deleted=True,
                                error=None
                            )
                        except Exception as delete_error:
                            print(f"  ⚠️ Failed to delete duplicate from Google Drive: {delete_error}", flush=True)
                            # Log deletion failure
                            try:
                                log_deletion(
                                    file_info={
                                        'file_id': file_id,
                                        'file_name': file_name,
                                        'original_name': file_name,
                                        'file_size_mb': 0,
                                        'renamed_to': None
                                    },
                                    validation_results={'duplicate': True},
                                    deleted=False,
                                    error=str(delete_error)
                                )
                            except:
                                pass  # Best effort logging

                        # Mark as processed in old system too
                        mark_as_processed(file_id)
                        continue

                    # [Phase 10-3] Register in unified registry before processing
                    print(f"  📝 Registering to unified registry...", flush=True)
                    registry.add_to_registry(
                        source='google_drive',
                        original_name=file_name,
                        user_display_name=user_display_name,
                        renamed_to=None,  # Will be updated after Phase 10-1 renames
                        file_id=file_id,
                        local_path=str(audio_path),
                        created_time=created_time  # ファイル作成時刻を追加
                    )

                    # Transcribe
                    print(f"[3/4] Transcribing and summarizing...", flush=True)
                    output = transcribe_file(audio_path)
                    print(output, flush=True)

                    # Mark as processed (before renaming, to prevent duplicate processing)
                    print(f"[4/4] Marking as processed...", flush=True)
                    mark_as_processed(file_id)
                    print(f"  Added to {PROCESSED_FILE}", flush=True)

                    # [Phase 10-1] Local rename is handled by structured_transcribe.py
                    # [Phase 10-2] Google Drive file will be deleted, so no need to rename on cloud

                    # [Phase 10-2] Auto-delete cloud files (after transcription completed)
                    # Always delete cloud files after successful transcription
                    try:
                        from src.utils.file_management.cloud_file_manager import (
                            SafeDeletionValidator,
                            delete_gdrive_file,
                            log_deletion,
                            get_file_size_mb
                        )

                        # Find the most recent structured JSON file
                        json_files = list(audio_path.parent.glob("*_structured.json"))
                        if json_files:
                            # Sort by modification time (newest first)
                            json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                            latest_json = json_files[0]

                            print(f"[Delete] Validating JSON integrity: {latest_json.name}", flush=True)

                            # Validate JSON integrity before deletion
                            validator = SafeDeletionValidator(latest_json)
                            validation_passed = validator.validate()
                            validation_results = validator.get_validation_details()

                            if validation_passed:
                                print(f"[Delete] ✅ Validation passed, deleting cloud file...", flush=True)

                                # Get file size for logging
                                file_size_mb = get_file_size_mb(service, file_id)

                                # Delete from Google Drive
                                deleted = False
                                error = None
                                try:
                                    delete_gdrive_file(service, file_id, file_name)
                                    deleted = True
                                    print(f"  ✅ Google Drive file deleted: {file_id}", flush=True)
                                except Exception as delete_error:
                                    error = str(delete_error)
                                    print(f"  ❌ Deletion failed: {error}", flush=True)

                                # Log deletion event
                                log_deletion(
                                    file_info={
                                        'file_id': file_id,
                                        'file_name': file_name,
                                        'original_name': file_name,
                                        'file_size_mb': file_size_mb,
                                        'json_path': latest_json
                                    },
                                    validation_results=validation_results,
                                    deleted=deleted,
                                    error=error
                                )

                            else:
                                print(f"[Delete] ❌ Validation failed, keeping cloud file", flush=True)
                                print(f"  Validation details: {validation_results}", flush=True)

                                # Log failed validation
                                log_deletion(
                                    file_info={
                                        'file_id': file_id,
                                        'file_name': file_name,
                                        'original_name': file_name,
                                        'json_path': latest_json
                                    },
                                    validation_results=validation_results,
                                    deleted=False,
                                    error="Validation failed"
                                )

                        else:
                            print(f"[Delete] Skipped: No structured JSON files found", flush=True)

                    except Exception as e:
                        print(f"[Warning] Auto-delete failed: {e}", flush=True)
                        print(f"  Cloud file is preserved", flush=True)
                        import traceback
                        print(f"  Traceback: {traceback.format_exc()}", flush=True)

                    print(f"[✓] Completed: {file_name}", flush=True)

                except Exception as e:
                    print(f"[✗] Error processing {file_name}: {e}", flush=True)
                    continue

        except Timeout:
            # Another thread is already processing this file
            print(f"[Skip] {file_name} is being processed by another thread", flush=True)
            continue


def setup_webhook(service, folder_id, webhook_url):
    """Setup Google Drive webhook notification"""
    # Calculate expiration time (24 hours from now)
    expiration_time = int((datetime.utcnow() + timedelta(hours=CHANNEL_EXPIRATION_HOURS)).timestamp() * 1000)

    # Create watch channel
    body = {
        'id': f'channel-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
        'type': 'web_hook',
        'address': webhook_url,
        'expiration': expiration_time
    }

    # Watch for changes
    response = service.changes().watch(
        pageToken=get_start_page_token(service),
        body=body
    ).execute()

    # Save channel info
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(response, f)

    print(f"[Webhook] Registered successfully")
    print(f"  Channel ID: {response.get('id')}")
    print(f"  Resource ID: {response.get('resourceId')}")
    print(f"  Expiration: {datetime.fromtimestamp(expiration_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")

    return response


async def auto_renew_webhook_task():
    """
    [Phase 15] Background task to automatically renew webhook channel
    Checks every RENEWAL_CHECK_INTERVAL_HOURS and renews if expiring soon
    """
    print(f"[Auto-Renewal] Background task started")
    print(f"[Auto-Renewal] Check interval: {RENEWAL_CHECK_INTERVAL_HOURS} hours")

    while True:
        try:
            # Wait for next check
            await asyncio.sleep(RENEWAL_CHECK_INTERVAL_HOURS * 3600)

            print(f"\n[Auto-Renewal] Checking webhook channel status...")

            # Check if channel exists and expiration time
            if not Path(CHANNEL_FILE).exists():
                print(f"[Auto-Renewal] No channel info file found, registering new webhook...")
                await register_new_webhook()
                continue

            # Load channel info
            with open(CHANNEL_FILE, 'r') as f:
                channel_info = json.load(f)

            expiration = channel_info.get('expiration')
            if not expiration:
                print(f"[Auto-Renewal] No expiration in channel info, registering new webhook...")
                await register_new_webhook()
                continue

            # Parse expiration time
            try:
                # Try parsing as ISO format first (for backward compatibility)
                expiry_dt = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # Parse as timestamp in milliseconds
                expiry_dt = datetime.fromtimestamp(int(expiration) / 1000, tz=timezone.utc)

            now = datetime.now(timezone.utc)
            time_until_expiry = (expiry_dt - now).total_seconds() / 3600  # hours

            print(f"[Auto-Renewal] Channel expires in {time_until_expiry:.1f} hours")

            # Renew if expiring within next 12 hours (half of 24h expiry)
            if time_until_expiry < 12:
                print(f"[Auto-Renewal] Channel expiring soon, renewing...")
                await register_new_webhook()
            else:
                print(f"[Auto-Renewal] Channel still valid, no renewal needed")

        except Exception as e:
            print(f"[Auto-Renewal] Error in renewal task: {e}")
            import traceback
            traceback.print_exc()
            # Continue running despite errors


async def register_new_webhook():
    """
    [Phase 15] Helper function to register new webhook
    Called by auto_renew_webhook_task
    """
    try:
        webhook_url = WEBHOOK_PUBLIC_URL
        if not webhook_url.endswith('/webhook'):
            webhook_url = webhook_url.rstrip('/') + '/webhook'

        print(f"[Auto-Renewal] Registering webhook to: {webhook_url}")

        service = get_drive_service()
        folder_id = get_root_folder_id()
        response = setup_webhook(service, folder_id, webhook_url)

        print(f"[Auto-Renewal] ✅ Webhook renewed successfully")
        return response

    except Exception as e:
        print(f"[Auto-Renewal] ❌ Failed to register webhook: {e}")
        import traceback
        traceback.print_exc()
        raise


# FastAPI app
app = FastAPI()


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook notifications from Google Drive"""
    headers = dict(request.headers)

    # Google Drive sends notifications with specific headers
    resource_state = headers.get('x-goog-resource-state')
    resource_id = headers.get('x-goog-resource-id')
    channel_id = headers.get('x-goog-channel-id')

    print(f"\n[Webhook] Received notification")
    print(f"  State: {resource_state}")
    print(f"  Resource ID: {resource_id}")
    print(f"  Channel ID: {channel_id}")

    if resource_state == 'sync':
        # Initial sync message, just acknowledge
        print("[Webhook] Sync message received (initial setup)")
        return {"status": "ok"}

    if resource_state in ['change', 'update']:
        # Process changes in background using thread
        print("[Debug] Starting background thread for checking changes...")
        thread = threading.Thread(target=check_for_changes_sync)
        thread.daemon = True
        thread.start()

    return {"status": "ok"}


def check_for_changes_sync():
    """Check for changes and process new files (synchronous version for threading)"""
    try:
        print("[Webhook] Checking for changes...", flush=True)
        print("[Debug] Getting Drive service...", flush=True)
        service = get_drive_service()
        print("[Debug] Got Drive service successfully", flush=True)

        folder_id = get_root_folder_id()
        print(f"[Debug] Folder ID: {folder_id}", flush=True)

        # Process new files
        print("[Debug] Calling process_new_files...", flush=True)
        process_new_files(service, folder_id)
        print("[Debug] process_new_files completed", flush=True)

    except Exception as e:
        print(f"[Error] Exception in check_for_changes: {e}", flush=True)
        import traceback
        traceback.print_exc()


@app.on_event("startup")
async def startup_event():
    """Setup webhook on startup"""
    print("=" * 60)
    print("Google Drive Webhook Server (My Drive Root)")
    print("=" * 60)
    print(f"Monitoring: My Drive root (audio files only)")
    print("Detection method: Real-time Push notifications\n")

    # Clean up old lock files from previous runs
    print("[Startup] Cleaning up stale lock files...")
    cleanup_old_locks()

    # [Phase 15] Auto-register webhook if enabled
    if ENABLE_AUTO_RENEWAL and WEBHOOK_PUBLIC_URL:
        print(f"[Startup] Auto-renewal enabled: {ENABLE_AUTO_RENEWAL}")
        print(f"[Startup] Public URL: {WEBHOOK_PUBLIC_URL}")

        try:
            # Construct full webhook URL
            webhook_url = WEBHOOK_PUBLIC_URL
            if not webhook_url.endswith('/webhook'):
                webhook_url = webhook_url.rstrip('/') + '/webhook'

            print(f"[Startup] Attempting to register webhook...")
            service = get_drive_service()
            folder_id = get_root_folder_id()
            response = setup_webhook(service, folder_id, webhook_url)

            print(f"[Startup] ✅ Webhook registered successfully")

            # Start background renewal task
            asyncio.create_task(auto_renew_webhook_task())
            print(f"[Startup] ✅ Auto-renewal task started (checks every {RENEWAL_CHECK_INTERVAL_HOURS}h)")

        except Exception as e:
            print(f"[Startup] ⚠️ Failed to register webhook: {e}")
            print(f"[Startup] Will continue without auto-renewal")
            import traceback
            traceback.print_exc()
    else:
        # Note: Webhook URL needs to be set manually after ngrok starts
        print("[Info] Auto-renewal disabled or WEBHOOK_PUBLIC_URL not set")
        print("[Info] Webhook setup will be done manually after getting tunnel URL")
        print("[Info] Use /setup endpoint to register webhook")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "service": "Google Drive Webhook Server"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Returns detailed status information
    """
    import psutil
    from datetime import datetime, timezone as tz

    # Check if channel is active
    channel_active = False
    channel_expires_at = None
    if Path(CHANNEL_FILE).exists():
        try:
            with open(CHANNEL_FILE, 'r') as f:
                channel_info = json.load(f)
                expiration = channel_info.get('expiration')
                if expiration:
                    channel_expires_at = expiration
                    # Check if not expired
                    # expiration is a timestamp in milliseconds (as string)
                    try:
                        # Try parsing as ISO format first (for backward compatibility)
                        expiry_dt = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # Parse as timestamp in milliseconds
                        expiry_dt = datetime.fromtimestamp(int(expiration) / 1000, tz=tz.utc)

                    if expiry_dt > datetime.now(tz.utc):
                        channel_active = True
        except Exception:
            pass

    # Get process info
    process = psutil.Process()

    return {
        "status": "healthy",
        "service": "Google Drive Webhook Server",
        "timestamp": datetime.now(tz.utc).isoformat(),
        "uptime_seconds": time.time() - process.create_time(),
        "channel_active": channel_active,
        "channel_expires_at": channel_expires_at,
        "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(interval=0.1),
        "download_dir": str(DOWNLOAD_DIR),
        "processed_files_registry": str(os.getenv('PROCESSED_FILES_REGISTRY'))
    }


@app.get("/setup")
async def setup_webhook_endpoint(webhook_url: str):
    """Manual webhook setup endpoint"""
    try:
        service = get_drive_service()
        folder_id = get_root_folder_id()
        # webhook_url should already include the /webhook path
        response = setup_webhook(service, folder_id, webhook_url)
        return {"status": "success", "channel": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
