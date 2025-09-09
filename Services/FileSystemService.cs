using System;
using System.IO;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Platform;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Services
{
    public class FileSystemService : IFileSystemService
    {
        private readonly IPlatformService _platformService;
        
        public FileSystemService(IPlatformService platformService)
        {
            _platformService = platformService;
            InitializeDirectories();
        }
        
        private void InitializeDirectories()
        {
            // Ensure all required directories exist
            CreateDirectory(GetAppDataPath());
            CreateDirectory(GetTailorPacksPath());
            CreateDirectory(GetLogsPath());
        }
        
        public string GetAppDataPath()
        {
            return _platformService.GetAppDataPath();
        }
        
        public string GetDocumentsPath()
        {
            return Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
        }
        
        public string GetTailorPacksPath()
        {
            return Path.Combine(GetAppDataPath(), "TailorPacks");
        }
        
        public string GetSettingsPath()
        {
            return Path.Combine(GetAppDataPath(), "settings.json");
        }
        
        public string GetLogsPath()
        {
            return Path.Combine(GetAppDataPath(), "Logs");
        }
        
        public bool FileExists(string path)
        {
            return File.Exists(path);
        }
        
        public bool DirectoryExists(string path)
        {
            return Directory.Exists(path);
        }
        
        public void CreateDirectory(string path)
        {
            if (!Directory.Exists(path))
            {
                Directory.CreateDirectory(path);
            }
        }
        
        public async Task<string> ReadAllTextAsync(string path)
        {
            return await File.ReadAllTextAsync(path);
        }
        
        public async Task WriteAllTextAsync(string path, string content)
        {
            // Ensure directory exists
            var directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            await File.WriteAllTextAsync(path, content);
        }
        
        public void DeleteFile(string path)
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        
        public void DeleteDirectory(string path, bool recursive = true)
        {
            if (Directory.Exists(path))
            {
                Directory.Delete(path, recursive);
            }
        }
        
        public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false)
        {
            if (!Directory.Exists(path))
                return Array.Empty<string>();
                
            var searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
            return Directory.GetFiles(path, searchPattern, searchOption);
        }
        
        public string[] GetDirectories(string path)
        {
            if (!Directory.Exists(path))
                return Array.Empty<string>();
                
            return Directory.GetDirectories(path);
        }
        
        public long GetFileSize(string path)
        {
            if (!File.Exists(path))
                return 0;
                
            var fileInfo = new FileInfo(path);
            return fileInfo.Length;
        }
        
        public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false)
        {
            // Ensure destination directory exists
            var directory = Path.GetDirectoryName(destinationPath);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            File.Copy(sourcePath, destinationPath, overwrite);
        }
        
        public void MoveFile(string sourcePath, string destinationPath)
        {
            // Ensure destination directory exists
            var directory = Path.GetDirectoryName(destinationPath);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            File.Move(sourcePath, destinationPath);
        }

        /// <summary>
        /// Save file asynchronously with progress reporting for large files
        /// </summary>
        public async Task SaveAsync(string path, byte[] data, IProgress<ProgressInfo>? progress = null)
        {
            await Task.Run(async () =>
            {
                try
                {
                    progress?.Report(new ProgressInfo(0, "Preparing to save file..."));
                    
                    // Ensure directory exists
                    var directory = Path.GetDirectoryName(path);
                    if (!string.IsNullOrEmpty(directory))
                    {
                        CreateDirectory(directory);
                    }

                    progress?.Report(new ProgressInfo(10, "Writing file..."));

                    // For large files, write in chunks to avoid blocking
                    const int bufferSize = 64 * 1024; // 64KB chunks
                    using var fileStream = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None, bufferSize, true);
                    
                    int totalBytes = data.Length;
                    int bytesWritten = 0;
                    
                    while (bytesWritten < totalBytes)
                    {
                        int chunkSize = Math.Min(bufferSize, totalBytes - bytesWritten);
                        await fileStream.WriteAsync(data, bytesWritten, chunkSize);
                        bytesWritten += chunkSize;
                        
                        // Report progress
                        int percentage = (int)((float)bytesWritten / totalBytes * 90) + 10; // 10-100%
                        progress?.Report(new ProgressInfo(percentage, $"Written {bytesWritten:N0} of {totalBytes:N0} bytes"));
                        
                        // Yield control to prevent blocking
                        if (bytesWritten % (bufferSize * 10) == 0)
                        {
                            await Task.Yield();
                        }
                    }
                    
                    await fileStream.FlushAsync();
                    progress?.Report(new ProgressInfo(100, "File saved successfully"));
                }
                catch (Exception ex)
                {
                    progress?.Report(new ProgressInfo(100, $"Save failed: {ex.Message}"));
                    throw;
                }
            });
        }

        /// <summary>
        /// Copy file asynchronously with progress reporting
        /// </summary>
        public async Task CopyFileAsync(string sourcePath, string destinationPath, bool overwrite = false, IProgress<ProgressInfo>? progress = null)
        {
            await Task.Run(async () =>
            {
                try
                {
                    progress?.Report(new ProgressInfo(0, "Starting file copy..."));
                    
                    if (!File.Exists(sourcePath))
                    {
                        throw new FileNotFoundException($"Source file not found: {sourcePath}");
                    }
                    
                    if (File.Exists(destinationPath) && !overwrite)
                    {
                        throw new InvalidOperationException($"Destination file already exists: {destinationPath}");
                    }

                    // Ensure destination directory exists
                    var directory = Path.GetDirectoryName(destinationPath);
                    if (!string.IsNullOrEmpty(directory))
                    {
                        CreateDirectory(directory);
                    }

                    progress?.Report(new ProgressInfo(10, "Copying file..."));

                    const int bufferSize = 64 * 1024; // 64KB buffer
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
                        
                        // Report progress
                        int percentage = (int)((float)bytesCopied / totalBytes * 90) + 10; // 10-100%
                        progress?.Report(new ProgressInfo(percentage, $"Copied {bytesCopied:N0} of {totalBytes:N0} bytes"));
                        
                        // Yield control periodically
                        if (bytesCopied % (bufferSize * 10) == 0)
                        {
                            await Task.Yield();
                        }
                    }
                    
                    await destinationStream.FlushAsync();
                    progress?.Report(new ProgressInfo(100, "File copied successfully"));
                }
                catch (Exception ex)
                {
                    progress?.Report(new ProgressInfo(100, $"Copy failed: {ex.Message}"));
                    throw;
                }
            });
        }
    }
}