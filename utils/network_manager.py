"""
WestfallPersonalAssistant Network Manager
Handles network requests with proper error handling and timeouts
"""

import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
import json
import logging
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from utils.error_handler import get_error_handler

class NetworkRequest(QThread):
    """Thread for network requests with proper error handling"""
    
    # Signals
    request_completed = pyqtSignal(bool, object, str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, url, method='get', params=None, data=None, json_data=None, 
                timeout=10, headers=None, max_retries=3, stream=False):
        super().__init__()
        self.url = url
        self.method = method.lower()
        self.params = params or {}
        self.data = data
        self.json_data = json_data
        self.timeout = timeout
        self.headers = headers or {}
        self.max_retries = max_retries
        self.stream = stream
        self.abort_flag = False
    
    def run(self):
        """Execute the request"""
        retries = 0
        
        while retries < self.max_retries and not self.abort_flag:
            try:
                # Select method
                if self.method == 'get':
                    response = requests.get(
                        self.url, 
                        params=self.params, 
                        timeout=self.timeout,
                        headers=self.headers,
                        stream=self.stream
                    )
                elif self.method == 'post':
                    response = requests.post(
                        self.url, 
                        params=self.params,
                        data=self.data,
                        json=self.json_data,
                        timeout=self.timeout,
                        headers=self.headers
                    )
                elif self.method == 'put':
                    response = requests.put(
                        self.url, 
                        params=self.params,
                        data=self.data,
                        json=self.json_data,
                        timeout=self.timeout,
                        headers=self.headers
                    )
                elif self.method == 'delete':
                    response = requests.delete(
                        self.url, 
                        params=self.params,
                        timeout=self.timeout,
                        headers=self.headers
                    )
                elif self.method == 'patch':
                    response = requests.patch(
                        self.url, 
                        params=self.params,
                        data=self.data,
                        json=self.json_data,
                        timeout=self.timeout,
                        headers=self.headers
                    )
                else:
                    self.request_completed.emit(False, None, f"Unsupported method: {self.method}")
                    return
                
                # Check if streaming response for large content
                if self.stream and response.status_code // 100 == 2:
                    # For streaming content like file downloads
                    self.request_completed.emit(True, response, "")
                    return
                
                # Check if successful
                if response.status_code // 100 == 2:  # 2xx status code
                    self.request_completed.emit(True, response, "")
                else:
                    # Retry server errors (5xx) but not client errors (4xx)
                    if response.status_code // 100 == 5 and retries < self.max_retries - 1:
                        retries += 1
                        continue
                    
                    self.request_completed.emit(
                        False, 
                        response, 
                        f"Server returned error: {response.status_code} - {response.reason}"
                    )
                
                return
                    
            except Timeout:
                if retries < self.max_retries - 1:
                    retries += 1
                    continue
                self.request_completed.emit(False, None, "Request timed out")
            except ConnectionError:
                if retries < self.max_retries - 1:
                    retries += 1
                    continue
                self.request_completed.emit(False, None, "Connection error")
            except RequestException as e:
                if retries < self.max_retries - 1:
                    retries += 1
                    continue
                self.request_completed.emit(False, None, str(e))
            except Exception as e:
                self.request_completed.emit(False, None, f"Unexpected error: {str(e)}")
            
            # If we get here, an error occurred
            if retries < self.max_retries - 1:
                retries += 1
            else:
                break
    
    def abort(self):
        """Abort the network request"""
        self.abort_flag = True

class NetworkManager(QObject):
    """Manager for network operations with proper error handling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending_requests = []
        self.error_handler = get_error_handler(parent)
    
    def get(self, url, params=None, callback=None, error_callback=None, 
           timeout=10, headers=None, max_retries=3):
        """Make GET request"""
        self._make_request('get', url, params=params, data=None, json_data=None,
                         callback=callback, error_callback=error_callback,
                         timeout=timeout, headers=headers, max_retries=max_retries)
    
    def post(self, url, data=None, json_data=None, params=None, callback=None,
            error_callback=None, timeout=10, headers=None, max_retries=3):
        """Make POST request"""
        self._make_request('post', url, params=params, data=data, json_data=json_data,
                         callback=callback, error_callback=error_callback,
                         timeout=timeout, headers=headers, max_retries=max_retries)
    
    def put(self, url, data=None, json_data=None, params=None, callback=None,
           error_callback=None, timeout=10, headers=None, max_retries=3):
        """Make PUT request"""
        self._make_request('put', url, params=params, data=data, json_data=json_data,
                         callback=callback, error_callback=error_callback,
                         timeout=timeout, headers=headers, max_retries=max_retries)
    
    def delete(self, url, params=None, callback=None, error_callback=None,
              timeout=10, headers=None, max_retries=3):
        """Make DELETE request"""
        self._make_request('delete', url, params=params, data=None, json_data=None,
                         callback=callback, error_callback=error_callback,
                         timeout=timeout, headers=headers, max_retries=max_retries)
    
    def patch(self, url, data=None, json_data=None, params=None, callback=None,
             error_callback=None, timeout=10, headers=None, max_retries=3):
        """Make PATCH request"""
        self._make_request('patch', url, params=params, data=data, json_data=json_data,
                         callback=callback, error_callback=error_callback,
                         timeout=timeout, headers=headers, max_retries=max_retries)
    
    def _make_request(self, method, url, params=None, data=None, json_data=None,
                     callback=None, error_callback=None, timeout=10, headers=None, 
                     max_retries=3, stream=False):
        """Internal method to make requests"""
        request = NetworkRequest(
            url=url, 
            method=method, 
            params=params, 
            data=data,
            json_data=json_data,
            timeout=timeout, 
            headers=headers, 
            max_retries=max_retries,
            stream=stream
        )
        
        # Connect signals
        request.request_completed.connect(
            lambda success, response, error: self._handle_response(
                success, response, error, callback, error_callback
            )
        )
        
        # Store request for tracking
        self.pending_requests.append(request)
        
        # Start the request
        request.start()
        
        return request
    
    def _handle_response(self, success, response, error, callback, error_callback):
        """Handle the response from a network request"""
        if success and callback:
            try:
                callback(response)
            except Exception as e:
                self.error_handler.handle_ui_error(e, "Error processing network response")
        elif not success and error_callback:
            try:
                error_callback(error)
            except Exception as e:
                self.error_handler.handle_ui_error(e, "Error handling network error")
        elif not success:
            # Default error handling
            self.error_handler.handle_network_error(error, "Network request failed")
    
    def download_file(self, url, file_path, progress_callback=None, callback=None, 
                     error_callback=None, timeout=30, headers=None, max_retries=3):
        """Download a file with progress tracking"""
        request = NetworkRequest(
            url=url,
            method='get',
            timeout=timeout,
            headers=headers,
            max_retries=max_retries,
            stream=True
        )
        
        def handle_download_response(success, response, error):
            if success:
                try:
                    with open(file_path, 'wb') as f:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback and total_size > 0:
                                    progress = int((downloaded / total_size) * 100)
                                    progress_callback(progress)
                    
                    if callback:
                        callback(file_path)
                        
                except Exception as e:
                    if error_callback:
                        error_callback(str(e))
                    else:
                        self.error_handler.handle_file_error(e, f"Failed to save file", file_path=file_path)
            else:
                if error_callback:
                    error_callback(error)
                else:
                    self.error_handler.handle_network_error(error, f"Failed to download file from {url}")
        
        request.request_completed.connect(handle_download_response)
        self.pending_requests.append(request)
        request.start()
        
        return request
    
    def upload_file(self, url, file_path, field_name='file', additional_data=None,
                   progress_callback=None, callback=None, error_callback=None,
                   timeout=60, headers=None, max_retries=3):
        """Upload a file with progress tracking"""
        try:
            with open(file_path, 'rb') as f:
                files = {field_name: f}
                data = additional_data or {}
                
                # Note: This is a simplified upload - for real progress tracking,
                # you'd need to use a custom adapter or library like requests-toolbelt
                request = NetworkRequest(
                    url=url,
                    method='post',
                    data=data,
                    timeout=timeout,
                    headers=headers,
                    max_retries=max_retries
                )
                
                request.request_completed.connect(
                    lambda success, response, error: self._handle_upload_response(
                        success, response, error, callback, error_callback
                    )
                )
                
                self.pending_requests.append(request)
                request.start()
                
                return request
                
        except Exception as e:
            if error_callback:
                error_callback(str(e))
            else:
                self.error_handler.handle_file_error(e, f"Failed to read file for upload", file_path=file_path)
            return None
    
    def _handle_upload_response(self, success, response, error, callback, error_callback):
        """Handle upload response"""
        if success and callback:
            try:
                callback(response)
            except Exception as e:
                self.error_handler.handle_ui_error(e, "Error processing upload response")
        elif not success and error_callback:
            try:
                error_callback(error)
            except Exception as e:
                self.error_handler.handle_ui_error(e, "Error handling upload error")
        elif not success:
            self.error_handler.handle_network_error(error, "File upload failed")
    
    def cancel_all_requests(self):
        """Cancel all pending requests"""
        for request in self.pending_requests:
            if request.isRunning():
                request.abort()
                request.wait()
        self.pending_requests.clear()
    
    def get_pending_requests_count(self):
        """Get number of pending requests"""
        return len([r for r in self.pending_requests if r.isRunning()])

# Global function to get a network manager instance
def get_network_manager(parent=None):
    """Get a new network manager instance"""
    return NetworkManager(parent)