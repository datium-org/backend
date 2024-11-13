from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import time
import threading
from queue import Queue
import os
import sys
from pathlib import Path
import logging
from typing import Dict, Set, Optional, NoReturn
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import json
from AppKit import (  # macOS specific
  NSWorkspace,
  NSFileManager,
  NSURL,
  NSString
)
from tqdm import tqdm

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s',
  handlers=[
    logging.FileHandler('webuploader.log'),
    logging.StreamHandler()
  ]
)
logger: logging.Logger = logging.getLogger(__name__)

class FileHandler(FileSystemEventHandler):
  def __init__(self, upload_queue: Queue[str]) -> None:
    super().__init__()
    self.upload_queue: Queue[str] = upload_queue
    self.processed_files: Set[str] = set()
    self.processed_events: Set[str] = set()  # Track event IDs to prevent duplicates

  def _generate_event_id(self, event_type: str, path: str, timestamp: float) -> str:
    """Generate a unique ID for an event to prevent duplicate processing"""
    return f"{event_type}:{path}:{timestamp}"

  def on_created(self, event: FileSystemEvent) -> None:
    """Handle file/directory creation events"""
    event_id = self._generate_event_id("created", event.src_path, time.time())
    if event_id in self.processed_events:
      return

    self.processed_events.add(event_id)
    if event.is_directory:
      logger.info(f"Directory created: {event.src_path}")
      # You might want to create this directory on the server
      print(f"Event: Directory created")
      print(f"Directory Path: {event.src_path}")
    else:
      logger.info(f"File created: {event.src_path}")
      print(f"Event: File created")
      print(f"File Path: {event.src_path}")
      if event.src_path not in self.processed_files:
        self.processed_files.add(event.src_path)
        self.upload_queue.put(event.src_path)
        
        def cleanup() -> None:
          time.sleep(5)
          self.processed_files.discard(event.src_path)
          self.processed_events.discard(event_id)
        
        threading.Thread(target=cleanup, daemon=True).start()

  def on_modified(self, event: FileSystemEvent) -> None:
    """Handle file/directory modification events"""
    event_id = self._generate_event_id("modified", event.src_path, time.time())
    if event_id in self.processed_events:
      return

    self.processed_events.add(event_id)
    if event.is_directory:
      return
    else:
      logger.info(f"File modified: {event.src_path}")
      print(f"Event: File modified")
      print(f"File Path: {event.src_path}")
      # Queue the modified file for upload
      if event.src_path not in self.processed_files:
        self.processed_files.add(event.src_path)
        self.upload_queue.put(event.src_path)
        
        def cleanup() -> None:
          time.sleep(5)
          self.processed_files.discard(event.src_path)
          self.processed_events.discard(event_id)
        
        threading.Thread(target=cleanup, daemon=True).start()

  def on_deleted(self, event: FileSystemEvent) -> None:
    """Handle file/directory deletion events"""
    if event.is_directory:
      logger.info(f"Directory deleted: {event.src_path}")
      print(f"Event: Directory deleted")
      print(f"Directory Path: {event.src_path}")
      # You might want to delete this directory on the server
    else:
      logger.info(f"File deleted: {event.src_path}")
      print(f"Event: File deleted")
      print(f"File Path: {event.src_path}")
      # You might want to delete this file from the server

  def on_moved(self, event: FileSystemEvent) -> None:
    """Handle file/directory move/rename events"""
    if event.is_directory:
      logger.info(f"Directory moved/renamed from {event.src_path} to {event.dest_path}")
      print(f"Event: Directory moved/renamed")
      print(f"From: {event.src_path}")
      print(f"To: {event.dest_path}")
      # You might want to move/rename this directory on the server
    else:
      logger.info(f"File moved/renamed from {event.src_path} to {event.dest_path}")
      print(f"Event: File moved/renamed")
      print(f"From: {event.src_path}")
      print(f"To: {event.dest_path}")
      # Queue the moved file for upload with new path
      if event.dest_path not in self.processed_files:
        self.processed_files.add(event.dest_path)
        self.upload_queue.put(event.dest_path)
        
        def cleanup() -> None:
          time.sleep(5)
          self.processed_files.discard(event.dest_path)
        
        threading.Thread(target=cleanup, daemon=True).start()

  def on_closed(self, event: FileSystemEvent) -> None:
    """Handle file close events (when a file is done being written)"""
    if not event.is_directory:
      logger.info(f"File closed: {event.src_path}")
      print(f"Event: File closed")
      print(f"File Path: {event.src_path}")
      # This might be a good time to ensure the file is fully uploaded

def create_sync_folder() -> str:
  """Create the sync folder in the user's home directory with proper macOS integration"""
  home: str = str(Path.home())
  sync_folder: str = os.path.join(home, "Documents", "WebUploadSync")
  
  if not os.path.exists(sync_folder):
    os.makedirs(sync_folder)
    
    # Make the folder look like a proper sync folder in Finder
    ws = NSWorkspace.sharedWorkspace()
    fm = NSFileManager.defaultManager()
    url = NSURL.fileURLWithPath_(sync_folder)
    
    logger.info(f"Created sync folder at: {sync_folder}")
  else:
    logger.info(f"Using existing sync folder at: {sync_folder}")
    
  return sync_folder

def upload_worker(queue: Queue[Optional[str]]) -> None:
  """Worker thread to handle file uploads"""
  while True:
    file_path: Optional[str] = queue.get()
    if file_path is None:  # Poison pill to stop the thread
      break
        
    # Simulate file upload
    file_name: str = os.path.basename(file_path)
    print(f"Uploading {file_name} to web server...")
    time.sleep(0.1)  # Simulate upload time without actually blocking
    print(f"Successfully uploaded {file_name}")
    
    queue.task_done()

def start_monitoring(folder_path: str) -> NoReturn:
  """Start monitoring the specified folder"""
  # Create a queue for managing upload tasks
  upload_queue: Queue[Optional[str]] = Queue()
  
  # Start the upload worker thread
  upload_thread: threading.Thread = threading.Thread(
    target=upload_worker, 
    args=(upload_queue,),
    daemon=True
  )
  upload_thread.start()
  
  # Initialize the event handler and observer
  event_handler: FileHandler = FileHandler(upload_queue)
  observer = Observer()
  observer.schedule(event_handler, folder_path, recursive=True)
  observer.start()
  
  try:
    print("Started file monitor...")
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print("\nStopping file monitor...")
    observer.stop()
    upload_queue.put(None)  # Send poison pill to stop upload thread
    observer.join()
    upload_thread.join()
    print("File monitor stopped successfully")

if __name__ == "__main__":
  # Create folder
  create_sync_folder()
  folder = os.path.join(str(Path.home()), "Documents", "WebUploadSync")

  TRACKED_FOLDER: str = folder  # Replace with your folder path
  start_monitoring(TRACKED_FOLDER)