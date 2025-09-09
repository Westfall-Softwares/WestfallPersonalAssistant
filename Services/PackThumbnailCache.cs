using System;
using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for caching pack thumbnails with efficient refresh operations
    /// </summary>
    public class PackThumbnailCache
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly Dictionary<string, string> _cache = new();
        private readonly string _cacheDirectory;

        public PackThumbnailCache(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _cacheDirectory = Path.Combine(_fileSystemService.GetAppDataPath(), "PackThumbnails");
        }

        /// <summary>
        /// Refreshes the thumbnail cache by scanning the specified directory
        /// </summary>
        /// <param name="path">Directory path to scan for thumbnails</param>
        /// <returns>Task representing the refresh operation</returns>
        public async Task RefreshAsync(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return;

            try
            {
                // PRIORITY A FIX: Add null-safe directory guard
                if (!Directory.Exists(path)) 
                    return; // Early return if directory doesn't exist

                // Clear existing cache for this path
                var pathKey = Path.GetFullPath(path);
                var keysToRemove = _cache.Keys.Where(k => k.StartsWith(pathKey)).ToList();
                foreach (var key in keysToRemove)
                {
                    _cache.Remove(key);
                }

                // Scan directory for thumbnail files
                foreach (var file in Directory.GetFiles(path))
                {
                    if (IsThumbnailFile(file))
                    {
                        await ProcessThumbnailFileAsync(file);
                    }
                }

                Console.WriteLine($"Thumbnail cache refreshed for path: {path}");
            }
            catch (UnauthorizedAccessException ex)
            {
                Console.WriteLine($"Access denied while refreshing thumbnails in {path}: {ex.Message}");
            }
            catch (IOException ex)
            {
                Console.WriteLine($"I/O error while refreshing thumbnails in {path}: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Unexpected error while refreshing thumbnails in {path}: {ex.Message}");
            }
        }

        /// <summary>
        /// Gets a cached thumbnail path for the specified pack
        /// </summary>
        /// <param name="packId">Pack identifier</param>
        /// <returns>Cached thumbnail path or null if not found</returns>
        public string? GetCachedThumbnail(string packId)
        {
            if (string.IsNullOrWhiteSpace(packId))
                return null;

            _cache.TryGetValue(packId, out var thumbnailPath);
            return thumbnailPath;
        }

        /// <summary>
        /// Checks if the specified file is a valid thumbnail file
        /// </summary>
        /// <param name="filePath">File path to check</param>
        /// <returns>True if the file is a thumbnail</returns>
        private bool IsThumbnailFile(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            return extension == ".png" || extension == ".jpg" || extension == ".jpeg" || extension == ".webp";
        }

        /// <summary>
        /// Processes a thumbnail file and adds it to the cache
        /// </summary>
        /// <param name="filePath">Path to the thumbnail file</param>
        /// <returns>Task representing the processing operation</returns>
        private async Task ProcessThumbnailFileAsync(string filePath)
        {
            try
            {
                var fileName = Path.GetFileNameWithoutExtension(filePath);
                var cacheKey = fileName;

                // Copy thumbnail to cache directory if needed
                var cachedPath = Path.Combine(_cacheDirectory, Path.GetFileName(filePath));
                
                if (!_fileSystemService.DirectoryExists(_cacheDirectory))
                {
                    _fileSystemService.CreateDirectory(_cacheDirectory);
                }

                if (!_fileSystemService.FileExists(cachedPath) || 
                    _fileSystemService.GetFileSize(filePath) != _fileSystemService.GetFileSize(cachedPath))
                {
                    _fileSystemService.CopyFile(filePath, cachedPath, overwrite: true);
                }

                _cache[cacheKey] = cachedPath;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error processing thumbnail {filePath}: {ex.Message}");
            }
        }

        /// <summary>
        /// Clears the entire thumbnail cache
        /// </summary>
        public void ClearCache()
        {
            _cache.Clear();
            Console.WriteLine("Thumbnail cache cleared");
        }
    }
}