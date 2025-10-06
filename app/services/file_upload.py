"""
File upload service for handling various file types with storage options.
"""
import os
import logging
import hashlib
import mimetypes
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from uuid import uuid4
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from PIL import Image
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.extensions import db
from app.models import UploadedFile, User
from app.services.base import BaseService
from app.config import Config

logger = logging.getLogger(__name__)


class FileUploadService(BaseService):
    """Service for handling file uploads with multiple storage backends."""
    
    model = UploadedFile
    
    # Allowed file types and their configurations
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'spreadsheet': {'xls', 'xlsx', 'csv'},
        'presentation': {'ppt', 'pptx'},
        'archive': {'zip', 'tar', 'gz', 'rar'},
        'code': {'py', 'js', 'html', 'css', 'json', 'xml'}
    }
    
    MAX_FILE_SIZES = {
        'image': 10 * 1024 * 1024,  # 10MB
        'document': 50 * 1024 * 1024,  # 50MB
        'spreadsheet': 25 * 1024 * 1024,  # 25MB
        'presentation': 100 * 1024 * 1024,  # 100MB
        'archive': 200 * 1024 * 1024,  # 200MB
        'code': 5 * 1024 * 1024  # 5MB
    }
    
    def __init__(self):
        self.s3_client = None
        self._init_s3()
        self._ensure_upload_directory()
    
    def _init_s3(self):
        """Initialize S3 client if configured."""
        try:
            aws_access_key = getattr(Config, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(Config, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(Config, 'AWS_REGION', 'us-east-1')
            
            if aws_access_key and aws_secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
                logger.info("S3 client initialized successfully")
            else:
                logger.info("S3 credentials not found, using local storage only")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {str(e)}")
    
    def _ensure_upload_directory(self):
        """Ensure upload directory exists."""
        upload_dir = getattr(Config, 'UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            logger.info(f"Created upload directory: {upload_dir}")
    
    @classmethod
    def _get_file_category(cls, filename: str) -> str:
        """Determine file category based on extension."""
        if not filename or '.' not in filename:
            return 'unknown'
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for category, extensions in cls.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return category
        
        return 'unknown'
    
    @classmethod
    def _validate_file(cls, file: FileStorage, allowed_categories: Optional[List[str]] = None) -> Tuple[bool, str, str]:
        """Validate uploaded file."""
        if not file:
            return False, "No file provided", ""
        
        if file.filename == '':
            return False, "No file selected", ""
        
        # Get file category
        category = cls._get_file_category(file.filename)
        
        if category == 'unknown':
            return False, "File type not allowed", ""
        
        if allowed_categories and category not in allowed_categories:
            return False, f"File category '{category}' not allowed", ""
        
        # Check file size (get size by seeking to end)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = cls.MAX_FILE_SIZES.get(category, 10 * 1024 * 1024)
        if file_size > max_size:
            return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB", ""
        
        return True, "", category
    
    def _generate_unique_filename(self, original_filename: str, user_id: str) -> str:
        """Generate unique filename to prevent conflicts."""
        secure_name = secure_filename(original_filename)
        name, ext = os.path.splitext(secure_name)
        
        # Create unique identifier
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid4())[:8]
        
        return f"{user_id}_{timestamp}_{unique_id}_{name}{ext}"
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def _save_to_local(self, file_content: bytes, filename: str) -> str:
        """Save file to local storage."""
        upload_dir = getattr(Config, 'UPLOAD_FOLDER', 'uploads')
        
        # Create subdirectories by date
        date_dir = datetime.utcnow().strftime('%Y/%m/%d')
        full_dir = os.path.join(upload_dir, date_dir)
        os.makedirs(full_dir, exist_ok=True)
        
        file_path = os.path.join(full_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return os.path.join(date_dir, filename)  # Return relative path
    
    def _save_to_s3(self, file_content: bytes, filename: str) -> str:
        """Save file to S3."""
        if not self.s3_client:
            raise Exception("S3 not configured")
        
        bucket_name = getattr(Config, 'S3_BUCKET_NAME', None)
        if not bucket_name:
            raise Exception("S3 bucket not configured")
        
        # Create S3 key with date structure
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        s3_key = f"{date_prefix}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            )
            return s3_key
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    def _process_image(self, file_content: bytes, max_width: int = 1920, max_height: int = 1080) -> bytes:
        """Process and resize image if needed."""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            # Resize if too large
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image processing failed: {str(e)}")
            return file_content  # Return original if processing fails
    
    def upload_file(
        self,
        file: FileStorage,
        user_id: str,
        storage_type: str = 'local',
        allowed_categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        process_images: bool = True
    ) -> UploadedFile:
        """
        Upload a file with specified storage backend.
        
        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            storage_type: 'local' or 's3'
            allowed_categories: List of allowed file categories
            metadata: Additional metadata to store
            process_images: Whether to process/resize images
        
        Returns:
            UploadedFile object
        """
        try:
            # Validate file
            is_valid, error_msg, category = self._validate_file(file, allowed_categories)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Read file content
            file.seek(0)
            file_content = file.read()
            file.seek(0)
            
            # Process images if needed
            if category == 'image' and process_images:
                file_content = self._process_image(file_content)
            
            # Generate unique filename
            unique_filename = self._generate_unique_filename(file.filename, user_id)
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(file_content)
            
            # Check for duplicate files
            existing_file = UploadedFile.query.filter(
                and_(
                    UploadedFile.file_hash == file_hash,
                    UploadedFile.uploaded_by == user_id
                )
            ).first()
            
            if existing_file:
                logger.info(f"Duplicate file detected: {file_hash}")
                return existing_file
            
            # Save file based on storage type
            if storage_type == 's3' and self.s3_client:
                file_path = self._save_to_s3(file_content, unique_filename)
            else:
                file_path = self._save_to_local(file_content, unique_filename)
                storage_type = 'local'  # Fallback to local if S3 fails
            
            # Create database record
            uploaded_file = UploadedFile(
                original_filename=file.filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=len(file_content),
                file_type=category,
                mime_type=file.mimetype or mimetypes.guess_type(file.filename)[0],
                file_hash=file_hash,
                storage_type=storage_type,
                uploaded_by=user_id,
                metadata=metadata or {}
            )
            
            db.session.add(uploaded_file)
            db.session.commit()
            
            logger.info(f"File uploaded successfully: {uploaded_file.id}")
            return uploaded_file
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    def get_file_url(self, file_id: int, user_id: str, expires_in: int = 3600) -> str:
        """
        Get URL for accessing a file.
        
        Args:
            file_id: ID of the file
            user_id: ID of the requesting user
            expires_in: URL expiration time in seconds (for S3)
        
        Returns:
            File access URL
        """
        try:
            uploaded_file = self.get_by_id(file_id)
            if not uploaded_file:
                raise ValueError("File not found")
            
            # Check permissions (owner or admin)
            if str(uploaded_file.uploaded_by) != user_id:
                user = User.query.get(user_id)
                if not user or user.role != 'admin':
                    raise PermissionError("Access denied")
            
            if uploaded_file.storage_type == 's3' and self.s3_client:
                # Generate presigned URL for S3
                bucket_name = getattr(Config, 'S3_BUCKET_NAME', None)
                if bucket_name:
                    try:
                        url = self.s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket_name, 'Key': uploaded_file.file_path},
                            ExpiresIn=expires_in
                        )
                        return url
                    except ClientError as e:
                        logger.error(f"Failed to generate S3 presigned URL: {str(e)}")
                        raise Exception("Failed to generate file URL")
            
            # Return local file URL
            base_url = getattr(Config, 'BASE_URL', 'http://localhost:5000')
            return f"{base_url}/api/files/{file_id}/download"
            
        except Exception as e:
            logger.error(f"Error getting file URL for {file_id}: {str(e)}")
            raise
    
    def delete_file(self, file_id: int, user_id: str) -> bool:
        """
        Delete a file from storage and database.
        
        Args:
            file_id: ID of the file to delete
            user_id: ID of the user requesting deletion
        
        Returns:
            True if successful
        """
        try:
            uploaded_file = self.get_by_id(file_id)
            if not uploaded_file:
                raise ValueError("File not found")
            
            # Check permissions
            if str(uploaded_file.uploaded_by) != user_id:
                user = User.query.get(user_id)
                if not user or user.role != 'admin':
                    raise PermissionError("Access denied")
            
            # Delete from storage
            if uploaded_file.storage_type == 's3' and self.s3_client:
                bucket_name = getattr(Config, 'S3_BUCKET_NAME', None)
                if bucket_name:
                    try:
                        self.s3_client.delete_object(
                            Bucket=bucket_name,
                            Key=uploaded_file.file_path
                        )
                    except ClientError as e:
                        logger.warning(f"Failed to delete from S3: {str(e)}")
            else:
                # Delete from local storage
                upload_dir = getattr(Config, 'UPLOAD_FOLDER', 'uploads')
                full_path = os.path.join(upload_dir, uploaded_file.file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            
            # Delete from database
            db.session.delete(uploaded_file)
            db.session.commit()
            
            logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise
    
    def get_user_files(
        self,
        user_id: str,
        file_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Get paginated list of user's files."""
        try:
            query = UploadedFile.query.filter(UploadedFile.uploaded_by == user_id)
            
            if file_type:
                query = query.filter(UploadedFile.file_type == file_type)
            
            query = query.order_by(desc(UploadedFile.created_at))
            
            # Paginate
            paginated = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            files = []
            for file_obj in paginated.items:
                file_dict = file_obj.to_dict()
                # Add download URL
                try:
                    file_dict['download_url'] = self.get_file_url(file_obj.id, user_id)
                except:
                    file_dict['download_url'] = None
                files.append(file_dict)
            
            return {
                'files': files,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
            
        except Exception as e:
            logger.error(f"Error getting user files for {user_id}: {str(e)}")
            raise
    
    def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            query = UploadedFile.query
            
            if user_id:
                query = query.filter(UploadedFile.uploaded_by == user_id)
            
            files = query.all()
            
            stats = {
                'total_files': len(files),
                'total_size': sum(f.file_size for f in files),
                'by_type': {},
                'by_storage': {'local': 0, 's3': 0}
            }
            
            for file_obj in files:
                # Count by file type
                if file_obj.file_type not in stats['by_type']:
                    stats['by_type'][file_obj.file_type] = {'count': 0, 'size': 0}
                stats['by_type'][file_obj.file_type]['count'] += 1
                stats['by_type'][file_obj.file_type]['size'] += file_obj.file_size
                
                # Count by storage type
                stats['by_storage'][file_obj.storage_type] += 1
            
            # Convert bytes to human readable
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            raise


# Import io module for image processing
import io
