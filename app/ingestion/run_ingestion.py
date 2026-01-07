import os
import sys
from tqdm import tqdm
from ingestion.sis_act import ingest_sis_act
from ingestion.ato_ruling import ingest_ato_ruling

def main():
    # 1. Define the tasks to be performed
    # Each task: (type, remote_path, unique_id/version)
    tasks = [
        ("legislation", "legislation/SIS_Act_2025_v1.pdf", "SIS_Act_2025_V1"),
        ("ruling", "rulings/TR_2021_3.pdf", "TR 2021/3"),
        ("ruling", "rulings/TR_2023_4.pdf", "TR 2023/4")
    ]

    print(f"🚀 Starting Ingestion Orchestrator for {len(tasks)} items...")

    # 2. Progress Bar wrapper
    for category, remote_key, identifier in tqdm(tasks, desc="Overall Progress"):
        try:
            if category == "legislation":
                # Ingest SIS Act with Versioning logic
                ingest_sis_act(remote_key=remote_key, version_tag=identifier)
            
            elif category == "ruling":
                # Ingest ATO Ruling with Ruling ID logic
                ingest_ato_ruling(remote_key=remote_key, ruling_id=identifier)
            
            print(f" ✅ Successfully processed {identifier}")
            
        except Exception as e:
            print(f" ❌ Failed to process {identifier}: {str(e)}")

    print("\n✨ All ingestion tasks completed.")

# from dotenv import load_dotenv
# load_dotenv()

if __name__ == "__main__":
    # Ensure environment variables are present before running - Refer API KEYS file
    required_vars = [
        "QDRANT_URL", "QDRANT_API_KEY", 
        "DO_SPACES_ENDPOINT", "DO_SPACES_KEY", 
        "DO_SPACES_SECRET", "DO_SPACES_BUCKET"
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"CRITICAL ERROR: Missing environment variables: {missing}")
        sys.exit(1)

    main()

    """
    How to use this in Codespaces
Configure .env: Ensure your terminal or .env file contains all your credentials (Qdrant and DigitalOcean).

Run as a Module: In the terminal, from the root directory, run:

Bash

python run_ingestion.py
    """

"""
Newer Version
-------------
import os
import sys
import json
import requests
from tqdm import tqdm
from ingestion.sis_act import ingest_sis_act
from ingestion.ato_ruling import ingest_ato_ruling

def send_slack_notification(message, color="#36a64f"):
    
    # Sends a formatted alert to a Slack channel via Incoming Webhook.
   
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Slack Webhook URL not set. Skipping notification.")
        return

    payload = {
        "attachments": [
            {
                "color": color,
                "text": message,
                "fallback": "Ingestion Update",
                "ts": None # Can be set to time.time() if needed
            }
        ]
    }

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(payload),
            headers={'Content-type': 'application/json'}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Failed to send Slack alert: {e}")

def main():
    tasks = [
        ("legislation", "legislation/SIS_Act_2025_v1.pdf", "SIS_Act_2025_V1"),
        ("ruling", "rulings/TR_2021_3.pdf", "TR 2021/3")
    ]

    print(f"🚀 Starting Ingestion Orchestrator for {len(tasks)} items...")
    send_slack_notification(f"🏁 *Batch Ingestion Started*: Processing {len(tasks)} documents.")

    success_count = 0
    for category, remote_key, identifier in tqdm(tasks, desc="Overall Progress"):
        try:
            if category == "legislation":
                ingest_sis_act(remote_key=remote_key, version_tag=identifier)
            elif category == "ruling":
                ingest_ato_ruling(remote_key=remote_key, ruling_id=identifier)
            
            success_count += 1
            
        except Exception as e:
            error_msg = f"❌ *Ingestion Error*: Failed on `{identifier}`\n> {str(e)}"
            send_slack_notification(error_msg, color="#eb4034")

    # Final Summary Notification
    summary = f"✅ *Batch Complete*\n- Total: {len(tasks)}\n- Succeeded: {success_count}\n- Failed: {len(tasks) - success_count}"
    send_slack_notification(summary)
    print("\n✨ All tasks finished. Summary sent to Slack.")

if __name__ == "__main__":
    main()
"""