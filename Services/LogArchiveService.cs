using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for archiving log files with async copy operations
    /// </summary>
    public class LogArchiveService
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly string _archiveDirectory;
        private readonly int _maxArchiveFiles;

        public LogArchiveService(IFileSystemService fileSystemService, int maxArchiveFiles = 10)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _maxArchiveFiles = maxArchiveFiles;
            _archiveDirectory = Path.Combine(_fileSystemService.GetAppDataPath(), "Logs", "Archive");
        }

        /// <summary>
        /// Archives the specified log file asynchronously
        /// </summary>
        /// <param name="sourceLogPath">Path to the source log file</param>
        /// <param name="progress">Optional progress reporter</param>
        /// <returns>Task representing the archive operation</returns>
        public async Task<bool> ArchiveAsync(string sourceLogPath, IProgress<ProgressInfo>? progress = null)
        {
            if (string.IsNullOrWhiteSpace(sourceLogPath))
            {
                throw new ArgumentException("Source log path cannot be null or empty", nameof(sourceLogPath));
            }

            if (!_fileSystemService.FileExists(sourceLogPath))
            {
                Console.WriteLine($"Source log file does not exist: {sourceLogPath}");
                return false;
            }

            try
            {
                progress?.Report(new ProgressInfo(0, "Starting log archive..."));

                // Ensure archive directory exists
                if (!_fileSystemService.DirectoryExists(_archiveDirectory))
                {
                    _fileSystemService.CreateDirectory(_archiveDirectory);
                }

                // Generate archive filename with timestamp
                var fileName = Path.GetFileName(sourceLogPath);
                var nameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                var extension = Path.GetExtension(fileName);
                var timestamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
                var archiveFileName = $"{nameWithoutExt}_{timestamp}{extension}";
                var destinationPath = Path.Combine(_archiveDirectory, archiveFileName);

                progress?.Report(new ProgressInfo(20, "Copying log file..."));

                // PRIORITY B FIX: Replace blocking File.Copy with async stream-based copy
                // OLD CODE: await Task.Run(() => File.Copy(src, dst, overwrite:true));
                // NEW CODE: Use stream-based async copy for non-blocking operation
                await CopyFileStreamBasedAsync(sourceLogPath, destinationPath, progress);

                progress?.Report(new ProgressInfo(80, "Cleaning up old archives..."));

                // Clean up old archive files
                await CleanupOldArchivesAsync();

                progress?.Report(new ProgressInfo(100, "Archive completed successfully"));

                Console.WriteLine($"Log file archived: {sourceLogPath} -> {destinationPath}");
                return true;
            }
            catch (Exception ex)
            {
                progress?.Report(new ProgressInfo(100, $"Archive failed: {ex.Message}"));
                Console.WriteLine($"Error archiving log file {sourceLogPath}: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Stream-based async file copy for non-blocking operation
        /// </summary>
        /// <param name="sourcePath">Source file path</param>
        /// <param name="destinationPath">Destination file path</param>
        /// <param name="progress">Optional progress reporter</param>
        /// <returns>Task representing the copy operation</returns>
        private async Task CopyFileStreamBasedAsync(string sourcePath, string destinationPath, IProgress<ProgressInfo>? progress = null)
        {
            const int bufferSize = 81920; // 80KB buffer
            
            using var sourceStream = new FileStream(sourcePath, FileMode.Open, FileAccess.Read, FileShare.Read, bufferSize, true);
            using var destinationStream = new FileStream(destinationPath, FileMode.Create, FileAccess.Write, FileShare.None, bufferSize, true);
            
            var buffer = new byte[bufferSize];
            long totalBytes = sourceStream.Length;
            long bytesCopied = 0;
            
            int bytesRead;
            while ((bytesRead = await sourceStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
            {
                await destinationStream.WriteAsync(buffer, 0, bytesRead);
                bytesCopied += bytesRead;
                
                // Report progress for large files
                if (totalBytes > 0)
                {
                    var progressPercent = 20 + (int)((bytesCopied * 60) / totalBytes); // 20-80% range
                    progress?.Report(new ProgressInfo(progressPercent, $"Copying... {bytesCopied}/{totalBytes} bytes"));
                }
            }
            
            await destinationStream.FlushAsync();
        }

        /// <summary>
        /// Alternative implementation using .NET 8+ File.CopyAsync (when available)
        /// This would be used when upgrading to .NET 8+
        /// </summary>
        private async Task CopyFileNet8Async(string sourcePath, string destinationPath)
        {
            // NOTE: This method would be used when upgrading to .NET 8+
            // await File.CopyAsync(sourcePath, destinationPath, overwrite: true);
            
            // For now, fall back to stream-based copy
            await CopyFileStreamBasedAsync(sourcePath, destinationPath);
        }

        /// <summary>
        /// Cleans up old archive files to maintain the specified limit
        /// </summary>
        /// <returns>Task representing the cleanup operation</returns>
        private async Task CleanupOldArchivesAsync()
        {
            try
            {
                var archiveFiles = _fileSystemService.GetFiles(_archiveDirectory, "*.log")
                    .OrderByDescending(f => File.GetLastWriteTime(f))
                    .ToArray();

                if (archiveFiles.Length > _maxArchiveFiles)
                {
                    var filesToDelete = archiveFiles.Skip(_maxArchiveFiles);
                    foreach (var file in filesToDelete)
                    {
                        _fileSystemService.DeleteFile(file);
                        await Task.Delay(10); // Small delay to avoid blocking
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error cleaning up archive files: {ex.Message}");
            }
        }

        /// <summary>
        /// Gets the current archive directory path
        /// </summary>
        /// <returns>Archive directory path</returns>
        public string GetArchiveDirectory()
        {
            return _archiveDirectory;
        }

        /// <summary>
        /// Gets the list of archived log files
        /// </summary>
        /// <returns>Array of archived log file paths</returns>
        public string[] GetArchivedFiles()
        {
            if (!_fileSystemService.DirectoryExists(_archiveDirectory))
                return Array.Empty<string>();

            return _fileSystemService.GetFiles(_archiveDirectory, "*.log")
                .OrderByDescending(f => File.GetLastWriteTime(f))
                .ToArray();
        }
    }
}