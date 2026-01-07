import os
import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

class DOSpacesHandler:
    def __init__(self):
        # 1. Collect variables
        region = os.getenv('DO_SPACES_REGION')
        endpoint = os.getenv('DO_SPACES_ENDPOINT')
        key = os.getenv('DO_SPACES_KEY')
        secret = os.getenv('DO_SPACES_SECRET')
        self.bucket_name = os.getenv('DO_SPACES_BUCKET')

        # 2. Validate that essential variables exist
        required_vars = {
            'DO_SPACES_REGION': region,
            'DO_SPACES_ENDPOINT': endpoint,
            'DO_SPACES_KEY': key,
            'DO_SPACES_SECRET': secret,
            'DO_SPACES_BUCKET': self.bucket_name
        }
        
        missing = [k for k, v in required_vars.items() if not v]
        if missing:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

        # 3. Initialize the session and client
        self.session = boto3.session.Session()
        self.client = self.session.client(
            's3',
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret
        )

    def list_files(self, prefix=""):
        """Lists files and generates a temporary download link for each."""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, 
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Skip the directory markers (0-byte objects ending in '/')
                if key.endswith('/'):
                    continue

                # Generate the temporary link (valid for 1 hour)
                download_url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=3600
                )

                files.append({
                    "name": key.split('/')[-1], # Just the filename for the UI
                    "path": key,                # Full path in the Space
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "download_url": download_url
                })
                
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
    
    def generate_download_url(self, file_key: str, expires_in: int = 3600):
        """
        Generates a temporary URL to download a file.
        :param file_key: The full path/name of the file in the Space.
        :param expires_in: Time in seconds before link expires (default 1 hour).
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
        
    def get_registry(self):
        """Reads registry.json from the root of the Space."""
        # try:
        #     response = self.client.get_object(Bucket=self.bucket_name, Key='registry.json')
        #     return json.loads(response['Body'].read().decode('utf-8'))
        # except ClientError as e:
        #     # If file doesn't exist, return an empty list or structure
        #     if e.response['Error']['Code'] == 'NoSuchKey':
        #         return {"indexed_files": []}
        #     return {"error": str(e)}
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key="registry.json")
            return json.loads(response['Body'].read().decode('utf-8'))
        except self.client.exceptions.NoSuchKey:
            # If the file doesn't exist, return a fresh template
            return {"indexed_files": []}
        except Exception as e:
            print(f"Error fetching registry: {e}")
            return {"indexed_files": []}

    def save_registry(self, registry_data):
        """
        Serializes and uploads the registry dictionary to DigitalOcean Spaces.
        """
        try:
            # 1. Convert dictionary to a JSON string
            # indent=2 makes it human-readable if you open it in a text editor
            json_data = json.dumps(registry_data, indent=2)

            # 2. Upload the string as a file
            self.client.put_object(
                Bucket=self.bucket_name,
                Key="registry.json",
                Body=json_data,
                ContentType='application/json',  # Important for browser viewing
                ACL='private'                    # Keep your registry private
            )
            return True
        except ClientError as e:
            print(f"Error saving registry to Spaces: {e}")
            return False
        except Exception as e:
            print(f"General error in save_registry: {e}")
            return False
    
    def delete_file(self, file_key: str):
        """Removes the file from the DigitalOcean Space."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except ClientError as e:
            print(f"Error deleting file from Spaces: {e}")
            return False