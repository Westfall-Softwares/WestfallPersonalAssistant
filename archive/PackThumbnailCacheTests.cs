using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Tests
{
    public class PackThumbnailCacheTests : IDisposable
    {
        private readonly string _tempDirectory;
        private readonly MockFileSystemService _mockFileSystemService;
        private readonly PackThumbnailCache _thumbnailCache;

        public PackThumbnailCacheTests()
        {
            _tempDirectory = Path.Combine(Path.GetTempPath(), $"PackThumbnailCacheTests_{Guid.NewGuid()}");
            Directory.CreateDirectory(_tempDirectory);
            
            _mockFileSystemService = new MockFileSystemService(_tempDirectory);
            _thumbnailCache = new PackThumbnailCache(_mockFileSystemService);
        }

        public void Dispose()
        {
            if (Directory.Exists(_tempDirectory))
            {
                Directory.Delete(_tempDirectory, true);
            }
        }

        [Fact]
        public async Task RefreshAsync_WithNonExistentDirectory_ShouldReturnWithoutError()
        {
            // Arrange
            var nonExistentPath = Path.Combine(_tempDirectory, "nonexistent");

            // Act & Assert - Should not throw
            await _thumbnailCache.RefreshAsync(nonExistentPath);
        }

        [Fact]
        public async Task RefreshAsync_WithNullPath_ShouldReturnWithoutError()
        {
            // Act & Assert - Should not throw
            await _thumbnailCache.RefreshAsync(null);
            await _thumbnailCache.RefreshAsync("");
            await _thumbnailCache.RefreshAsync("   ");
        }

        [Fact]
        public async Task RefreshAsync_WithValidDirectory_ShouldProcessThumbnails()
        {
            // Arrange
            var testDir = Path.Combine(_tempDirectory, "thumbnails");
            Directory.CreateDirectory(testDir);
            
            // Create a test image file
            var imageFile = Path.Combine(testDir, "test.png");
            await File.WriteAllTextAsync(imageFile, "fake png content");

            // Act
            await _thumbnailCache.RefreshAsync(testDir);

            // Assert
            var cachedThumbnail = _thumbnailCache.GetCachedThumbnail("test");
            Assert.NotNull(cachedThumbnail);
        }

        [Fact]
        public void GetCachedThumbnail_WithNullOrEmptyPackId_ShouldReturnNull()
        {
            // Act & Assert
            Assert.Null(_thumbnailCache.GetCachedThumbnail(null));
            Assert.Null(_thumbnailCache.GetCachedThumbnail(""));
            Assert.Null(_thumbnailCache.GetCachedThumbnail("   "));
        }

        [Fact]
        public void ClearCache_ShouldClearAllCachedThumbnails()
        {
            // Act & Assert - Should not throw
            _thumbnailCache.ClearCache();
        }

        // Mock FileSystemService for testing
        private class MockFileSystemService : IFileSystemService
        {
            private readonly string _basePath;

            public MockFileSystemService(string basePath)
            {
                _basePath = basePath;
            }

            public string GetAppDataPath() => _basePath;
            public string GetDocumentsPath() => Path.Combine(_basePath, "Documents");
            public bool FileExists(string path) => File.Exists(path);
            public bool DirectoryExists(string path) => Directory.Exists(path);
            public void CreateDirectory(string path) => Directory.CreateDirectory(path);
            public Task<string> ReadAllTextAsync(string path) => File.ReadAllTextAsync(path);
            public Task WriteAllTextAsync(string path, string content) => File.WriteAllTextAsync(path, content);
            public void DeleteFile(string path) => File.Delete(path);
            public void DeleteDirectory(string path, bool recursive = true) => Directory.Delete(path, recursive);
            public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false)
                => Directory.GetFiles(path, searchPattern, recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
            public string[] GetDirectories(string path) => Directory.GetDirectories(path);
            public long GetFileSize(string path) => new FileInfo(path).Length;
            public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false) 
                => File.Copy(sourcePath, destinationPath, overwrite);
            public void MoveFile(string sourcePath, string destinationPath) => File.Move(sourcePath, destinationPath);
            public string GetTailorPacksPath() => Path.Combine(_basePath, "TailorPacks");
            public string GetSettingsPath() => Path.Combine(_basePath, "settings.json");
            public string GetLogsPath() => Path.Combine(_basePath, "Logs");
        }
    }
}