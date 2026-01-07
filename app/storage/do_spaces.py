import os
import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

class DOSpacesHandler:
    def __init__(self):
        self.session = boto3.session.Session()
        self.client = self.session.client(
            's3',
            region_name=os.getenv('DO_SPACES_REGION'),
            endpoint_url=os.getenv('DO_SPACES_ENDPOINT'),
            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
        )
        self.bucket_name = os.getenv('DO_SPACES_BUCKET')

    def list_files(self, prefix=""):
        """Lists files in the Space."""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, 
                Prefix=prefix
            )
            files = [
                {"name": obj['Key'], "size": obj['Size'], "last_modified": obj['LastModified']}
                for obj in response.get('Contents', [])
            ]
            return files
        except ClientError as e:
            print(f"Error listing files: {e}")
            return []

    def get_file_content(self, file_key):
        """Reads a file's content into memory."""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error reading file {file_key}: {e}")
            return None
    
    def get_registry(self):
        """Reads registry.json from the root of the Space."""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key='registry.json')
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            # If file doesn't exist, return an empty list or structure
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {"indexed_files": []}
            return {"error": str(e)}

    def save_registry(self, registry_data):
        """Writes the updated registry.json back to the Space."""
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key='registry.json',
                Body=json.dumps(registry_data, indent=4),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False