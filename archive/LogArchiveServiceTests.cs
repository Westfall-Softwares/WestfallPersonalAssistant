using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Tests
{
    public class LogArchiveServiceTests : IDisposable
    {
        private readonly string _tempDirectory;
        private readonly MockFileSystemService _mockFileSystemService;
        private readonly LogArchiveService _logArchiveService;

        public LogArchiveServiceTests()
        {
            _tempDirectory = Path.Combine(Path.GetTempPath(), $"LogArchiveServiceTests_{Guid.NewGuid()}");
            Directory.CreateDirectory(_tempDirectory);
            
            _mockFileSystemService = new MockFileSystemService(_tempDirectory);
            _logArchiveService = new LogArchiveService(_mockFileSystemService, maxArchiveFiles: 3);
        }

        public void Dispose()
        {
            if (Directory.Exists(_tempDirectory))
            {
                Directory.Delete(_tempDirectory, true);
            }
        }

        [Fact]
        public async Task ArchiveAsync_WithNullPath_ShouldThrowArgumentException()
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _logArchiveService.ArchiveAsync(null));
            await Assert.ThrowsAsync<ArgumentException>(() => _logArchiveService.ArchiveAsync(""));
            await Assert.ThrowsAsync<ArgumentException>(() => _logArchiveService.ArchiveAsync("   "));
        }

        [Fact]
        public async Task ArchiveAsync_WithNonExistentFile_ShouldReturnFalse()
        {
            // Arrange
            var nonExistentFile = Path.Combine(_tempDirectory, "nonexistent.log");

            // Act
            var result = await _logArchiveService.ArchiveAsync(nonExistentFile);

            // Assert
            Assert.False(result);
        }

        [Fact]
        public async Task ArchiveAsync_WithValidFile_ShouldReturnTrueAndCreateArchive()
        {
            // Arrange
            var logFile = Path.Combine(_tempDirectory, "test.log");
            await File.WriteAllTextAsync(logFile, "Test log content");

            // Act
            var result = await _logArchiveService.ArchiveAsync(logFile);

            // Assert
            Assert.True(result);
            
            // Verify archive directory and files exist
            var archiveDir = _logArchiveService.GetArchiveDirectory();
            Assert.True(Directory.Exists(archiveDir));
            
            var archivedFiles = _logArchiveService.GetArchivedFiles();
            Assert.NotEmpty(archivedFiles);
        }

        [Fact]
        public async Task ArchiveAsync_WithProgressReporting_ShouldCallProgressCallback()
        {
            // Arrange
            var logFile = Path.Combine(_tempDirectory, "test.log");
            await File.WriteAllTextAsync(logFile, "Test log content");
            
            var progressReported = false;
            var progress = new Progress<ProgressInfo>(info =>
            {
                progressReported = true;
                Assert.NotNull(info.Message);
                Assert.InRange(info.Percentage, 0, 100);
            });

            // Act
            var result = await _logArchiveService.ArchiveAsync(logFile, progress);

            // Assert
            Assert.True(result);
            Assert.True(progressReported);
        }

        [Fact]
        public void GetArchiveDirectory_ShouldReturnValidPath()
        {
            // Act
            var archiveDir = _logArchiveService.GetArchiveDirectory();

            // Assert
            Assert.NotNull(archiveDir);
            Assert.Contains("Archive", archiveDir);
        }

        [Fact]
        public void GetArchivedFiles_WithNoArchives_ShouldReturnEmptyArray()
        {
            // Act
            var archivedFiles = _logArchiveService.GetArchivedFiles();

            // Assert
            Assert.NotNull(archivedFiles);
            Assert.Empty(archivedFiles);
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