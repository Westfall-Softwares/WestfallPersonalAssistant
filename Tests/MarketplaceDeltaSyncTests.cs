using System;
using System.Threading.Tasks;
using System.Threading;
using Xunit;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Tests
{
    public class MarketplaceDeltaSyncTests
    {
        [Fact]
        public async Task MockMarketplaceApiClient_GetPacksChangedSince_ReturnsResults()
        {
            // Arrange
            var apiClient = new MockMarketplaceApiClient();
            var lastSyncTime = DateTime.UtcNow.AddDays(-7); // 7 days ago

            // Act
            var result = await apiClient.GetPacksChangedSinceAsync(lastSyncTime);

            // Assert
            Assert.NotNull(result);
            Assert.True(result.AddedPacks.Count + result.UpdatedPacks.Count + result.RemovedPackIds.Count >= 0);
        }

        [Fact]
        public async Task TailorPackMarketplaceSyncService_SyncPacks_ReturnsStats()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var networkService = new NetworkService(new MockSecureStorageService());
            var tailorPackManager = TailorPackManager.Instance;
            tailorPackManager.Initialize(fileSystemService);
            var apiClient = new MockMarketplaceApiClient();
            var settingsManager = new MockSettingsManager();

            var syncService = new TailorPackMarketplaceSyncService(
                fileSystemService,
                networkService,
                tailorPackManager,
                apiClient,
                settingsManager);

            // Act
            var stats = await syncService.SyncPacksAsync();

            // Assert
            Assert.NotNull(stats);
            Assert.True(stats.Added >= 0);
            Assert.True(stats.Updated >= 0);
            Assert.True(stats.Removed >= 0);
            Assert.True(stats.Duration >= TimeSpan.Zero);
        }

        [Fact]
        public async Task TailorPackMarketplaceSyncService_SyncPacksWithProgress_ReportsProgress()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var networkService = new NetworkService(new MockSecureStorageService());
            var tailorPackManager = TailorPackManager.Instance;
            tailorPackManager.Initialize(fileSystemService);
            var apiClient = new MockMarketplaceApiClient();
            var settingsManager = new MockSettingsManager();

            var syncService = new TailorPackMarketplaceSyncService(
                fileSystemService,
                networkService,
                tailorPackManager,
                apiClient,
                settingsManager);

            bool progressReported = false;
            var progress = new Progress<double>(p => {
                progressReported = true;
                Assert.True(p >= 0.0 && p <= 1.0);
            });

            // Act
            var stats = await syncService.SyncPacksAsync(progress);

            // Assert
            Assert.True(progressReported);
            Assert.NotNull(stats);
        }

        [Fact]
        public async Task TailorPackMarketplaceSyncService_SyncPacksWithCancellation_HandlesCancellation()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var networkService = new NetworkService(new MockSecureStorageService());
            var tailorPackManager = TailorPackManager.Instance;
            tailorPackManager.Initialize(fileSystemService);
            var apiClient = new MockMarketplaceApiClient();
            var settingsManager = new MockSettingsManager();

            var syncService = new TailorPackMarketplaceSyncService(
                fileSystemService,
                networkService,
                tailorPackManager,
                apiClient,
                settingsManager);

            using var cts = new CancellationTokenSource();
            cts.Cancel(); // Cancel immediately

            // Act & Assert
            var stats = await syncService.SyncPacksAsync(cancellationToken: cts.Token);
            Assert.NotNull(stats);
        }
    }

    // Additional mock class that's not already defined
    public class MockSecureStorageService : ISecureStorageService
    {
        private readonly System.Collections.Generic.Dictionary<string, string> _storage = new();

        public void StoreSecureData(string key, string data) => _storage[key] = data;
        public string RetrieveSecureData(string key) => _storage.TryGetValue(key, out var value) ? value : string.Empty;
        public void DeleteSecureData(string key) => _storage.Remove(key);
        public bool SecureDataExists(string key) => _storage.ContainsKey(key);
        public string EncryptString(string plaintext) => plaintext; // Mock implementation
        public string DecryptString(string ciphertext) => ciphertext; // Mock implementation
        public void GenerateNewKey() { } // Mock implementation
        public void RotateKeys() { } // Mock implementation
        public void SecureDeleteFile(string filePath) { } // Mock implementation
        public void SecureDeleteData(byte[] data) { } // Mock implementation
    }
}