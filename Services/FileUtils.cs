using System;
using System.IO;
using System.Threading.Tasks;
using System.Security.Cryptography;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Unified file operations utility class to reduce code duplication
    /// Provides secure, async file operations with proper error handling
    /// </summary>
    public static class FileUtils
    {
        private const int DefaultBufferSize = 4096;
        private const int MaxFilePathLength = 260;

        /// <summary>
        /// Asynchronously reads all text from a file with proper error handling
        /// </summary>
        public static async Task<string> ReadTextAsync(string path)
        {
            ValidateFilePath(path);

            try
            {
                using var stream = new FileStream(
                    path, 
                    FileMode.Open, 
                    FileAccess.Read, 
                    FileShare.Read, 
                    bufferSize: DefaultBufferSize, 
                    useAsync: true);
                using var reader = new StreamReader(stream);
                return await reader.ReadToEndAsync();
            }
            catch (FileNotFoundException)
            {
                throw new FileNotFoundException($"The file '{path}' was not found.");
            }
            catch (DirectoryNotFoundException)
            {
                throw new DirectoryNotFoundException($"The directory for file '{path}' was not found.");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while reading file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Asynchronously writes text to a file with directory creation and proper error handling
        /// </summary>
        public static async Task WriteTextAsync(string path, string content)
        {
            ValidateFilePath(path);
            
            if (content == null)
                throw new ArgumentNullException(nameof(content));

            try
            {
                // Create directory if it doesn't exist
                var directory = Path.GetDirectoryName(path);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                using var stream = new FileStream(
                    path, 
                    FileMode.Create, 
                    FileAccess.Write, 
                    FileShare.None, 
                    bufferSize: DefaultBufferSize, 
                    useAsync: true);
                using var writer = new StreamWriter(stream);
                await writer.WriteAsync(content);
                await writer.FlushAsync();
            }
            catch (DirectoryNotFoundException)
            {
                throw new DirectoryNotFoundException($"Could not create directory for file '{path}'.");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to write file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while writing file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Asynchronously reads all bytes from a file with proper error handling
        /// </summary>
        public static async Task<byte[]> ReadBytesAsync(string path)
        {
            ValidateFilePath(path);

            try
            {
                using var stream = new FileStream(
                    path, 
                    FileMode.Open, 
                    FileAccess.Read, 
                    FileShare.Read, 
                    bufferSize: DefaultBufferSize, 
                    useAsync: true);
                
                var buffer = new byte[stream.Length];
                int totalBytesRead = 0;
                int bytesRead;
                
                while (totalBytesRead < buffer.Length)
                {
                    bytesRead = await stream.ReadAsync(buffer, totalBytesRead, buffer.Length - totalBytesRead);
                    if (bytesRead == 0)
                        break;
                    totalBytesRead += bytesRead;
                }
                
                return buffer;
            }
            catch (FileNotFoundException)
            {
                throw new FileNotFoundException($"The file '{path}' was not found.");
            }
            catch (DirectoryNotFoundException)
            {
                throw new DirectoryNotFoundException($"The directory for file '{path}' was not found.");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while reading file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Asynchronously writes bytes to a file with directory creation and proper error handling
        /// </summary>
        public static async Task WriteBytesAsync(string path, byte[] bytes)
        {
            ValidateFilePath(path);
            
            if (bytes == null)
                throw new ArgumentNullException(nameof(bytes));

            try
            {
                // Create directory if it doesn't exist
                var directory = Path.GetDirectoryName(path);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                using var stream = new FileStream(
                    path, 
                    FileMode.Create, 
                    FileAccess.Write, 
                    FileShare.None, 
                    bufferSize: DefaultBufferSize, 
                    useAsync: true);
                
                await stream.WriteAsync(bytes, 0, bytes.Length);
                await stream.FlushAsync();
            }
            catch (DirectoryNotFoundException)
            {
                throw new DirectoryNotFoundException($"Could not create directory for file '{path}'.");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to write file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while writing file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Validates if a file path is valid and safe to use
        /// </summary>
        public static bool IsValidPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return false;

            try
            {
                // Check for invalid characters
                var invalidChars = Path.GetInvalidPathChars();
                foreach (char c in path)
                {
                    if (Array.IndexOf(invalidChars, c) >= 0)
                        return false;
                }

                // Check path length
                if (path.Length > MaxFilePathLength)
                    return false;

                // Try to get full path (this will throw if path is invalid)
                var fullPath = Path.GetFullPath(path);
                var root = Path.GetPathRoot(fullPath);
                
                return !string.IsNullOrEmpty(root);
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Safely copies a file with overwrite option and proper error handling
        /// </summary>
        public static async Task CopyFileAsync(string sourcePath, string destinationPath, bool overwrite = false)
        {
            ValidateFilePath(sourcePath);
            ValidateFilePath(destinationPath);

            if (!File.Exists(sourcePath))
                throw new FileNotFoundException($"Source file '{sourcePath}' does not exist.");

            if (!overwrite && File.Exists(destinationPath))
                throw new InvalidOperationException($"Destination file '{destinationPath}' already exists and overwrite is disabled.");

            try
            {
                // Create destination directory if it doesn't exist
                var destinationDirectory = Path.GetDirectoryName(destinationPath);
                if (!string.IsNullOrEmpty(destinationDirectory) && !Directory.Exists(destinationDirectory))
                {
                    Directory.CreateDirectory(destinationDirectory);
                }

                // Use async copy for better performance with large files
                using var sourceStream = new FileStream(sourcePath, FileMode.Open, FileAccess.Read, FileShare.Read, DefaultBufferSize, true);
                using var destinationStream = new FileStream(destinationPath, FileMode.Create, FileAccess.Write, FileShare.None, DefaultBufferSize, true);
                
                await sourceStream.CopyToAsync(destinationStream);
                await destinationStream.FlushAsync();
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied while copying from '{sourcePath}' to '{destinationPath}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while copying from '{sourcePath}' to '{destinationPath}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Safely deletes a file if it exists
        /// </summary>
        public static void DeleteFileIfExists(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return;

            try
            {
                if (File.Exists(path))
                {
                    File.Delete(path);
                }
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied while deleting file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while deleting file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Gets file size safely with proper error handling
        /// </summary>
        public static long GetFileSize(string path)
        {
            ValidateFilePath(path);

            try
            {
                var fileInfo = new FileInfo(path);
                return fileInfo.Exists ? fileInfo.Length : 0;
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied while accessing file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while accessing file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Checks if a file exists safely
        /// </summary>
        public static bool FileExists(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return false;

            try
            {
                return File.Exists(path);
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Creates a directory if it doesn't exist
        /// </summary>
        public static void EnsureDirectoryExists(string directoryPath)
        {
            if (string.IsNullOrWhiteSpace(directoryPath))
                throw new ArgumentException("Directory path cannot be null or empty", nameof(directoryPath));

            try
            {
                if (!Directory.Exists(directoryPath))
                {
                    Directory.CreateDirectory(directoryPath);
                }
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied while creating directory '{directoryPath}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while creating directory '{directoryPath}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Computes SHA-256 hash of a file
        /// </summary>
        public static async Task<string> ComputeFileHashAsync(string path)
        {
            ValidateFilePath(path);

            try
            {
                using var sha256 = SHA256.Create();
                using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, DefaultBufferSize, true);
                
                var hashBytes = await Task.Run(() => sha256.ComputeHash(stream));
                return Convert.ToBase64String(hashBytes);
            }
            catch (FileNotFoundException)
            {
                throw new FileNotFoundException($"The file '{path}' was not found.");
            }
            catch (UnauthorizedAccessException)
            {
                throw new UnauthorizedAccessException($"Access denied to file '{path}'.");
            }
            catch (IOException ex)
            {
                throw new IOException($"An I/O error occurred while computing hash for file '{path}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Validates a file path and throws appropriate exceptions if invalid
        /// </summary>
        private static void ValidateFilePath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                throw new ArgumentException("File path cannot be null or empty", nameof(path));

            if (!IsValidPath(path))
                throw new ArgumentException($"Invalid file path: '{path}'", nameof(path));
        }
    }
}