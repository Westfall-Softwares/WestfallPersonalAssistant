using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Tests
{
    public class LargeDatabaseExportServiceTests
    {
        private class MockDatabaseService : IDatabaseService
        {
            public Task InitializeAsync() => Task.CompletedTask;
            public Task<int> ExecuteNonQueryAsync(string sql, params object[] parameters) => Task.FromResult(1);
            public Task<T?> ExecuteScalarAsync<T>(string sql, params object[] parameters) where T : struct => Task.FromResult<T?>(default(T));
            public Task<T[]> QueryAsync<T>(string sql, Func<object[], T> mapper, params object[] parameters) => Task.FromResult(Array.Empty<T>());
            public bool DatabaseExists() => true;
            public long GetDatabaseSize() => 1024 * 1024; // 1MB
            public Task OptimizeDatabaseAsync() => Task.CompletedTask;
            public Task<bool> BackupDatabaseAsync(string backupPath) => Task.FromResult(true);
            public Task<bool> RestoreDatabaseAsync(string backupPath) => Task.FromResult(true);
        }

        private class MockFileSystemService : IFileSystemService
        {
            public string GetAppDataPath() => "/test/path";
            public string GetDocumentsPath() => "/test/documents";
            public string GetTailorPacksPath() => "/test/tailorpacks";
            public string GetSettingsPath() => "/test/settings.json";
            public string GetLogsPath() => "/test/logs";
            public bool FileExists(string path) => true;
            public bool DirectoryExists(string path) => true;
            public void CreateDirectory(string path) { }
            public Task<string> ReadAllTextAsync(string path) => Task.FromResult("test content");
            public Task WriteAllTextAsync(string path, string content) => Task.CompletedTask;
            public void DeleteFile(string path) { }
            public void DeleteDirectory(string path, bool recursive = true) { }
            public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false) => Array.Empty<string>();
            public string[] GetDirectories(string path) => Array.Empty<string>();
            public long GetFileSize(string path) => 1024;
            public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false) { }
            public void MoveFile(string sourcePath, string destinationPath) { }
            public Task SaveAsync(string path, byte[] data, IProgress<ProgressInfo>? progress = null) => Task.CompletedTask;
            public Task CopyFileAsync(string sourcePath, string destinationPath, bool overwrite = false, IProgress<ProgressInfo>? progress = null) => Task.CompletedTask;
        }

        [Fact]
        public async Task ExportDatabaseAsync_WithProgress_ReportsProgress()
        {
            // Arrange
            var dbService = new MockDatabaseService();
            var fileService = new MockFileSystemService();
            var exportService = new LargeDatabaseExportService(dbService, fileService);
            
            double lastProgress = 0;
            int progressCallCount = 0;
            var progress = new Progress<double>(p => 
            {
                lastProgress = p;
                progressCallCount++;
            });

            // Act
            var result = await exportService.ExportDatabaseAsync("/test/export.db", progress);

            // Assert
            Assert.True(result);
            Assert.True(progressCallCount > 0, "Progress callback should be called at least once");
            Assert.True(lastProgress >= 0.0 && lastProgress <= 1.0, $"Progress should be between 0.0 and 1.0, but was {lastProgress}");
        }

        [Fact]
        public async Task ExportDatabaseWithDetailedProgressAsync_ReportsDetailedProgress()
        {
            // Arrange
            var dbService = new MockDatabaseService();
            var fileService = new MockFileSystemService();
            var exportService = new LargeDatabaseExportService(dbService, fileService);
            
            var progressMessages = new System.Collections.Generic.List<string>();
            var progress = new Progress<ProgressInfo>(info => progressMessages.Add(info.Message));

            // Act
            var result = await exportService.ExportDatabaseWithDetailedProgressAsync("/test/export.db", progress);

            // Assert
            Assert.True(result);
            Assert.NotEmpty(progressMessages);
            Assert.Contains(progressMessages, m => m.Contains("Starting database export"));
            Assert.Contains(progressMessages, m => m.Contains("successful"));
        }

        [Fact]
        public void Constructor_WithNullDatabaseService_ThrowsArgumentNullException()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentNullException>(() => 
                new LargeDatabaseExportService(null, new MockFileSystemService()));
        }

        [Fact]
        public void Constructor_WithNullFileSystemService_ThrowsArgumentNullException()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentNullException>(() => 
                new LargeDatabaseExportService(new MockDatabaseService(), null));
        }
    }
}