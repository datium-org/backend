# interactions/shared/s3_client/s3_client.py

import os
import logging
from typing import Optional, List, Dict
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Client:
  """
  A client for interacting with AWS S3 or compatible services like MinIO,
  encapsulating common operations such as uploading, downloading, listing, and deleting objects.
  """

  def __init__(
    self,
    bucket_name: str,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    endpoint_url: Optional[str] = None,  # For MinIO or LocalStack
    use_ssl: bool = True,
    verify_ssl: bool = True,
    s3_config: Optional[Dict] = None
  ):
    """
    Initializes the S3Client with necessary configurations.

    :param bucket_name: Name of the S3 bucket to interact with.
    :param aws_access_key_id: AWS access key ID. If None, uses environment variable.
    :param aws_secret_access_key: AWS secret access key. If None, uses environment variable.
    :param aws_region: AWS region name. If None, uses environment variable.
    :param endpoint_url: Custom endpoint URL (e.g., MinIO, LocalStack). If None, uses AWS S3.
    :param use_ssl: Whether to use SSL for connection.
    :param verify_ssl: Whether to verify SSL certificates.
    :param s3_config: Additional configuration for Boto3 client.
    """
    self.bucket_name = bucket_name
    self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
    self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
    self.aws_region = aws_region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    self.endpoint_url = endpoint_url
    self.use_ssl = use_ssl
    self.verify_ssl = verify_ssl

    # Default Boto3 client configuration
    self.boto_config = Config(
      signature_version='s3v4',
      retries={
        'max_attempts': 10,
        'mode': 'standard'
      },
      connect_timeout=5,
      read_timeout=30
    )

    # Merge additional S3 configurations if provided
    if s3_config:
      for key, value in s3_config.items():
        setattr(self.boto_config, key, value)

    # Initialize the S3 client
    self.s3_client = boto3.client(
      's3',
      aws_access_key_id=self.aws_access_key_id,
      aws_secret_access_key=self.aws_secret_access_key,
      region_name=self.aws_region,
      endpoint_url=self.endpoint_url,
      use_ssl=self.use_ssl,
      verify=self.verify_ssl,
      config=self.boto_config
    )

    # Ensure the bucket exists
    self._ensure_bucket_exists()

  def _ensure_bucket_exists(self):
    """
    Checks if the specified bucket exists. If not, creates it.
    """
    try:
      self.s3_client.head_bucket(Bucket=self.bucket_name)
      logger.info(f"Bucket '{self.bucket_name}' exists.")
    except ClientError as e:
      error_code = int(e.response['Error']['Code'])
      if error_code == 404:
        try:
          self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': self.aws_region}
          )
          logger.info(f"Bucket '{self.bucket_name}' created.")
        except ClientError as ce:
          logger.error(f"Failed to create bucket '{self.bucket_name}': {ce}")
          raise
      else:
        logger.error(f"Error checking bucket '{self.bucket_name}': {e}")
        raise

  def upload_file(
    self,
    file_path: str,
    object_name: Optional[str] = None,
    extra_args: Optional[Dict] = None
  ) -> bool:
    """
    Uploads a file to the specified S3 bucket.

    :param file_path: Path to the local file to upload.
    :param object_name: S3 object name. If None, uses the basename of the file_path.
    :param extra_args: Additional arguments for upload (e.g., ACL, ServerSideEncryption).
                        If not provided, applies SSE only if not using a custom endpoint.
    :return: True if upload was successful, False otherwise.
    """
    if object_name is None:
      object_name = os.path.basename(file_path)

    # Determine if SSE should be applied
    if self.endpoint_url:
      # Likely using MinIO or similar; do not apply SSE unless explicitly specified
      upload_extra_args = extra_args or {}
    else:
      # Using AWS S3; apply default SSE if not overridden
      upload_extra_args = extra_args or {
          'ServerSideEncryption': 'AES256'  # Default encryption
      }

    try:
      self.s3_client.upload_file(
        Filename=file_path,
        Bucket=self.bucket_name,
        Key=object_name,
        ExtraArgs=upload_extra_args
      )
      logger.info(f"File '{file_path}' uploaded as '{object_name}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to upload '{file_path}' to '{self.bucket_name}/{object_name}': {e}")
      return False

  def download_file(
    self,
    object_name: str,
    file_path: str,
    extra_args: Optional[Dict] = None
  ) -> bool:
    """
    Downloads a file from the specified S3 bucket.

    :param object_name: S3 object name to download.
    :param file_path: Path to save the downloaded file.
    :param extra_args: Additional arguments for download.
    :return: True if download was successful, False otherwise.
    """
    try:
      self.s3_client.download_file(
        Bucket=self.bucket_name,
        Key=object_name,
        Filename=file_path,
        ExtraArgs=extra_args or {}
      )
      logger.info(f"File '{object_name}' downloaded to '{file_path}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to download '{object_name}' from '{self.bucket_name}': {e}")
      return False

  def list_files(self, prefix: Optional[str] = None) -> List[str]:
    """
    Lists all files in the specified S3 bucket, optionally filtered by a prefix.

    :param prefix: Prefix to filter objects (e.g., folder name).
    :return: List of object keys.
    """
    try:
      paginator = self.s3_client.get_paginator('list_objects_v2')
      page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix or '')

      objects = []
      for page in page_iterator:
        if 'Contents' in page:
          for obj in page['Contents']:
            objects.append(obj['Key'])
      logger.info(f"Listed {len(objects)} files in bucket '{self.bucket_name}'.")
      return objects
    except ClientError as e:
      logger.error(f"Failed to list files in bucket '{self.bucket_name}': {e}")
      return []

  def delete_file(self, object_name: str) -> bool:
    """
    Deletes a file from the specified S3 bucket.

    :param object_name: S3 object name to delete.
    :return: True if deletion was successful, False otherwise.
    """
    try:
      self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
      logger.info(f"File '{object_name}' deleted from bucket '{self.bucket_name}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to delete '{object_name}' from '{self.bucket_name}': {e}")
      return False

  def generate_presigned_url(
    self,
    object_name: str,
    expiration: int = 3600,
    method: str = 'get_object'
  ) -> Optional[str]:
    """
    Generates a pre-signed URL for accessing an object.

    :param object_name: S3 object name.
    :param expiration: Time in seconds for the pre-signed URL to remain valid.
    :param method: Method for the pre-signed URL ('get_object' or 'put_object').
    :return: Pre-signed URL as a string, or None if generation failed.
    """
    try:
      url = self.s3_client.generate_presigned_url(
        ClientMethod=method,
        Params={'Bucket': self.bucket_name, 'Key': object_name},
        ExpiresIn=expiration
      )
      logger.info(f"Generated pre-signed URL for '{object_name}': {url}")
      return url
    except ClientError as e:
      logger.error(f"Failed to generate pre-signed URL for '{object_name}': {e}")
      return None

  def copy_file(
    self,
    source_object: str,
    destination_object: str,
    extra_args: Optional[Dict] = None
  ) -> bool:
    """
    Copies a file within the same bucket or to a different bucket.

    :param source_object: Source S3 object key.
    :param destination_object: Destination S3 object key.
    :param extra_args: Additional arguments for copy (e.g., ACL, Metadata).
    :return: True if copy was successful, False otherwise.
    """
    copy_source = {'Bucket': self.bucket_name, 'Key': source_object}
    try:
      self.s3_client.copy(
        CopySource=copy_source,
        Bucket=self.bucket_name,
        Key=destination_object,
        ExtraArgs=extra_args or {}
      )
      logger.info(f"Copied '{source_object}' to '{destination_object}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to copy '{source_object}' to '{destination_object}': {e}")
      return False

  def object_exists(self, object_name: str) -> bool:
    """
    Checks if an object exists in the S3 bucket.

    :param object_name: S3 object name.
    :return: True if the object exists, False otherwise.
    """
    try:
      self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
      logger.info(f"Object '{object_name}' exists in bucket '{self.bucket_name}'.")
      return True
    except ClientError as e:
      if e.response['Error']['Code'] == '404':
        logger.info(f"Object '{object_name}' does not exist in bucket '{self.bucket_name}'.")
        return False
      else:
        logger.error(f"Error checking existence of '{object_name}': {e}")
        return False

  def get_object_metadata(self, object_name: str) -> Optional[Dict]:
    """
    Retrieves metadata of an object in the S3 bucket.

    :param object_name: S3 object name.
    :return: Dictionary of metadata if object exists, None otherwise.
    """
    try:
      response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
      metadata = {
        'LastModified': response['LastModified'],
        'ContentLength': response['ContentLength'],
        'ContentType': response.get('ContentType'),
        'ETag': response.get('ETag'),
        'Metadata': response.get('Metadata')
      }
      logger.info(f"Retrieved metadata for '{object_name}': {metadata}")
      return metadata
    except ClientError as e:
      logger.error(f"Failed to retrieve metadata for '{object_name}': {e}")
      return None

  def set_object_acl(self, object_name: str, acl: str = 'private') -> bool:
    """
    Sets the Access Control List (ACL) for an object.

    :param object_name: S3 object name.
    :param acl: ACL policy (e.g., 'private', 'public-read').
    :return: True if ACL was set successfully, False otherwise.
    """
    try:
      self.s3_client.put_object_acl(Bucket=self.bucket_name, Key=object_name, ACL=acl)
      logger.info(f"Set ACL for '{object_name}' to '{acl}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to set ACL for '{object_name}': {e}")
      return False

  def delete_multiple_files(self, object_names: List[str]) -> bool:
    """
    Deletes multiple objects from the S3 bucket.

    :param object_names: List of S3 object names to delete.
    :return: True if all deletions were successful, False otherwise.
    """
    if not object_names:
      logger.info("No objects provided for deletion.")
      return True

    delete_requests = [{'Key': obj} for obj in object_names]
    try:
      response = self.s3_client.delete_objects(
        Bucket=self.bucket_name,
        Delete={'Objects': delete_requests, 'Quiet': True}
      )
      deleted = response.get('Deleted', [])
      logger.info(f"Deleted {len(deleted)} objects from bucket '{self.bucket_name}'.")
      return True
    except ClientError as e:
      logger.error(f"Failed to delete multiple objects: {e}")
      return False

  # Additional methods can be added here (e.g., lifecycle management, tagging, etc.)
