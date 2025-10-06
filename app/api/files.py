"""
File upload API endpoints for handling file operations.
"""
from flask import request, jsonify, send_file, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import logging

from app.services.file_upload import FileUploadService
from app.models import User
from app.utils.decorators import handle_exceptions, role_required

logger = logging.getLogger(__name__)


class FileUploadResource(Resource):
    """Resource for file upload operations."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def post(self):
        """Upload a file."""
        try:
            user_id = get_jwt_identity()
            
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': 'No file provided'
                }), 400
            
            file = request.files['file']
            
            # Get optional parameters
            storage_type = request.form.get('storage_type', 'local')
            allowed_categories = request.form.getlist('allowed_categories')
            process_images = request.form.get('process_images', 'true').lower() == 'true'
            
            # Get metadata from form
            metadata = {}
            if 'description' in request.form:
                metadata['description'] = request.form['description']
            if 'tags' in request.form:
                metadata['tags'] = request.form['tags'].split(',')
            if 'category' in request.form:
                metadata['category'] = request.form['category']
            
            # Upload file
            uploaded_file = self.file_service.upload_file(
                file=file,
                user_id=user_id,
                storage_type=storage_type,
                allowed_categories=allowed_categories if allowed_categories else None,
                metadata=metadata,
                process_images=process_images
            )
            
            return jsonify({
                'success': True,
                'data': uploaded_file.to_dict(),
                'message': 'File uploaded successfully'
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to upload file'
            }), 500


class FileListResource(Resource):
    """Resource for listing user's files."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get list of user's uploaded files."""
        try:
            user_id = get_jwt_identity()
            
            # Get query parameters
            file_type = request.args.get('file_type')
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 50)
            
            # Get files
            files_data = self.file_service.get_user_files(
                user_id=user_id,
                file_type=file_type,
                page=page,
                per_page=per_page
            )
            
            return jsonify({
                'success': True,
                'data': files_data
            })
            
        except Exception as e:
            logger.error(f"Error getting file list: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve files'
            }), 500


class FileDetailResource(Resource):
    """Resource for individual file operations."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def get(self, file_id):
        """Get file details."""
        try:
            user_id = get_jwt_identity()
            
            uploaded_file = self.file_service.get_by_id(file_id)
            if not uploaded_file:
                return jsonify({
                    'success': False,
                    'message': 'File not found'
                }), 404
            
            # Check permissions
            if str(uploaded_file.uploaded_by) != user_id:
                user = User.query.get(user_id)
                if not user or user.role != 'admin':
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            
            # Get file details with download URL
            file_data = uploaded_file.to_dict()
            file_data['download_url'] = self.file_service.get_file_url(file_id, user_id)
            
            return jsonify({
                'success': True,
                'data': file_data
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error getting file details for {file_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve file details'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    def delete(self, file_id):
        """Delete a file."""
        try:
            user_id = get_jwt_identity()
            
            success = self.file_service.delete_file(file_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'File deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete file'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to delete file'
            }), 500


class FileDownloadResource(Resource):
    """Resource for file download."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def get(self, file_id):
        """Download a file."""
        try:
            user_id = get_jwt_identity()
            
            uploaded_file = self.file_service.get_by_id(file_id)
            if not uploaded_file:
                return jsonify({
                    'success': False,
                    'message': 'File not found'
                }), 404
            
            # Check permissions
            if str(uploaded_file.uploaded_by) != user_id:
                user = User.query.get(user_id)
                if not user or user.role != 'admin':
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            
            # For S3 files, redirect to presigned URL
            if uploaded_file.storage_type == 's3':
                download_url = self.file_service.get_file_url(file_id, user_id)
                return jsonify({
                    'success': True,
                    'download_url': download_url,
                    'redirect': True
                })
            
            # For local files, serve the file directly
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_dir, uploaded_file.file_path)
            
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'message': 'File not found on disk'
                }), 404
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=uploaded_file.original_filename,
                mimetype=uploaded_file.mime_type
            )
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to download file'
            }), 500


class FileUrlResource(Resource):
    """Resource for getting file access URLs."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def get(self, file_id):
        """Get file access URL."""
        try:
            user_id = get_jwt_identity()
            expires_in = request.args.get('expires_in', 3600, type=int)
            
            # Limit expiration time
            expires_in = min(expires_in, 86400)  # Max 24 hours
            
            url = self.file_service.get_file_url(
                file_id=file_id,
                user_id=user_id,
                expires_in=expires_in
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'url': url,
                    'expires_in': expires_in
                }
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error getting file URL for {file_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get file URL'
            }), 500


class FileStorageStatsResource(Resource):
    """Resource for storage statistics."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get storage usage statistics."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            # Regular users get their own stats, admins can see all
            if user.role == 'admin' and request.args.get('all') == 'true':
                stats = self.file_service.get_storage_stats()
            else:
                stats = self.file_service.get_storage_stats(user_id)
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get storage statistics'
            }), 500


class FileBulkOperationsResource(Resource):
    """Resource for bulk file operations."""
    
    def __init__(self):
        self.file_service = FileUploadService()
    
    @jwt_required()
    @handle_exceptions
    def post(self):
        """Perform bulk operations on files."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            operation = data.get('operation')
            file_ids = data.get('file_ids', [])
            
            if not operation or not file_ids:
                return jsonify({
                    'success': False,
                    'message': 'Operation and file_ids are required'
                }), 400
            
            results = {'success': [], 'failed': []}
            
            if operation == 'delete':
                for file_id in file_ids:
                    try:
                        success = self.file_service.delete_file(file_id, user_id)
                        if success:
                            results['success'].append(file_id)
                        else:
                            results['failed'].append({'file_id': file_id, 'error': 'Delete failed'})
                    except Exception as e:
                        results['failed'].append({'file_id': file_id, 'error': str(e)})
            
            elif operation == 'get_urls':
                for file_id in file_ids:
                    try:
                        url = self.file_service.get_file_url(file_id, user_id)
                        results['success'].append({'file_id': file_id, 'url': url})
                    except Exception as e:
                        results['failed'].append({'file_id': file_id, 'error': str(e)})
            
            else:
                return jsonify({
                    'success': False,
                    'message': f'Unsupported operation: {operation}'
                }), 400
            
            return jsonify({
                'success': True,
                'data': results,
                'message': f'Bulk {operation} completed'
            })
            
        except Exception as e:
            logger.error(f"Error in bulk operations: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Bulk operation failed'
            }), 500


class FileValidationResource(Resource):
    """Resource for file validation and info."""
    
    @jwt_required()
    @handle_exceptions
    def post(self):
        """Validate file before upload."""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': 'No file provided'
                }), 400
            
            file = request.files['file']
            allowed_categories = request.form.getlist('allowed_categories')
            
            # Validate file
            is_valid, error_msg, category = FileUploadService._validate_file(
                file, 
                allowed_categories if allowed_categories else None
            )
            
            # Get file info
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            validation_result = {
                'is_valid': is_valid,
                'category': category,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'filename': file.filename,
                'mime_type': file.mimetype
            }
            
            if not is_valid:
                validation_result['error'] = error_msg
            else:
                max_size = FileUploadService.MAX_FILE_SIZES.get(category, 10 * 1024 * 1024)
                validation_result['max_size_mb'] = max_size // (1024 * 1024)
                validation_result['within_size_limit'] = file_size <= max_size
            
            return jsonify({
                'success': True,
                'data': validation_result
            })
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'File validation failed'
            }), 500


# Register routes
def register_file_routes(api):
    """Register file management API routes."""
    api.add_resource(FileUploadResource, '/api/files/upload')
    api.add_resource(FileListResource, '/api/files')
    api.add_resource(FileDetailResource, '/api/files/<int:file_id>')
    api.add_resource(FileDownloadResource, '/api/files/<int:file_id>/download')
    api.add_resource(FileUrlResource, '/api/files/<int:file_id>/url')
    api.add_resource(FileStorageStatsResource, '/api/files/stats')
    api.add_resource(FileBulkOperationsResource, '/api/files/bulk')
    api.add_resource(FileValidationResource, '/api/files/validate')
