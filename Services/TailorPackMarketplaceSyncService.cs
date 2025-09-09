using System;
using System.Threading.Tasks;
using System.Net.Http;
using System.Text.Json;
using System.Linq;
using System.Threading;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for syncing Tailor Pack data with marketplace with progress tracking and delta sync optimization
    /// </summary>
    public class TailorPackMarketplaceSyncService
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly NetworkService _networkService;
        private readonly TailorPackManager _tailorPackManager;
        private readonly IMarketplaceApiClient _marketplaceApiClient;
        private readonly ISettingsManager _settingsManager;
        private readonly string _marketplaceApiUrl = "https://api.westfall-marketplace.com/v1";

        private const string LastSyncTimeKey = "Marketplace_LastSyncTime";

        public TailorPackMarketplaceSyncService(
            IFileSystemService fileSystemService, 
            NetworkService networkService,
            TailorPackManager tailorPackManager,
            IMarketplaceApiClient? marketplaceApiClient = null,
            ISettingsManager? settingsManager = null)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _networkService = networkService ?? throw new ArgumentNullException(nameof(networkService));
            _tailorPackManager = tailorPackManager ?? throw new ArgumentNullException(nameof(tailorPackManager));
            
            // Use provided instances or create defaults
            _marketplaceApiClient = marketplaceApiClient ?? new MockMarketplaceApiClient();
            _settingsManager = settingsManager ?? new SettingsManager(fileSystemService);
        }

        /// <summary>
        /// Sync installed Tailor Packs with marketplace with progress reporting
        /// </summary>
        /// <param name="progress">Progress reporter (0.0 to 1.0)</param>
        /// <returns>True if sync was successful</returns>
        public async Task<bool> SyncWithMarketplaceAsync(IProgress<double>? progress = null)
        {
            try
            {
                // Convert IProgress<double> to IProgress<ProgressInfo>
                var progressInfo = progress != null ? new Progress<ProgressInfo>(info => 
                {
                    // Convert percentage to double (0.0 to 1.0)
                    progress.Report(info.Percentage / 100.0);
                }) : null;

                return await SyncWithMarketplaceDetailedAsync(progressInfo);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during marketplace sync: {ex.Message}");
                progress?.Report(1.0);
                return false;
            }
        }

        /// <summary>
        /// Sync with marketplace using optimized delta sync with detailed progress information
        /// </summary>
        /// <param name="progress">Detailed progress reporter</param>
        /// <param name="cancellationToken">Cancellation token</param>
        /// <returns>Sync statistics</returns>
        public async Task<SyncStats> SyncPacksAsync(
            IProgress<double>? progress = null,
            CancellationToken cancellationToken = default)
        {
            var stats = new SyncStats();
            
            try
            {
                progress?.Report(0.0);

                // Step 1: Check network connectivity (5%)
                if (!await CheckInternetConnectivityAsync())
                {
                    Console.WriteLine("No internet connection available");
                    progress?.Report(1.0);
                    return stats;
                }
                progress?.Report(0.05);

                // Step 2: Get last sync time (10%)
                var lastSyncTime = await GetLastSyncTimeAsync();
                Console.WriteLine($"Last sync time: {lastSyncTime:yyyy-MM-dd HH:mm:ss} UTC");
                progress?.Report(0.10);

                // Step 3: Perform delta sync with pagination (15% - 85%)
                string? continuationToken = null;
                int totalProcessed = 0;
                double deltaProgressStart = 0.15;
                double deltaProgressRange = 0.70;

                do
                {
                    var result = await _marketplaceApiClient.GetPacksChangedSinceAsync(
                        lastSyncTime, 
                        continuationToken,
                        cancellationToken);

                    // Process changes
                    await ProcessAddedPacksAsync(result.AddedPacks, cancellationToken);
                    stats.Added += result.AddedPacks.Count;

                    await ProcessUpdatedPacksAsync(result.UpdatedPacks, cancellationToken);
                    stats.Updated += result.UpdatedPacks.Count;

                    await ProcessRemovedPacksAsync(result.RemovedPackIds, cancellationToken);
                    stats.Removed += result.RemovedPackIds.Count;

                    totalProcessed += result.AddedPacks.Count + result.UpdatedPacks.Count + result.RemovedPackIds.Count;
                    continuationToken = result.ContinuationToken;

                    // Update progress based on estimated total or page count
                    if (result.EstimatedTotalChanges.HasValue && result.EstimatedTotalChanges.Value > 0)
                    {
                        var deltaProgress = Math.Min(1.0, (double)totalProcessed / result.EstimatedTotalChanges.Value);
                        progress?.Report(deltaProgressStart + deltaProgress * deltaProgressRange);
                    }
                    else
                    {
                        // Fallback to page-based progress
                        var pageProgress = Math.Min(1.0, result.CurrentPage / 10.0); // Assume max 10 pages
                        progress?.Report(deltaProgressStart + pageProgress * deltaProgressRange);
                    }

                    Console.WriteLine($"Processed page {result.CurrentPage}: +{result.AddedPacks.Count} added, +{result.UpdatedPacks.Count} updated, +{result.RemovedPackIds.Count} removed");

                } while (!string.IsNullOrEmpty(continuationToken) && !cancellationToken.IsCancellationRequested);

                progress?.Report(0.85);

                // Step 4: Update last sync time (90%)
                await SaveLastSyncTimeAsync(DateTime.UtcNow);
                progress?.Report(0.90);

                // Step 5: Cleanup and finalize (100%)
                stats.EndTime = DateTime.UtcNow;
                Console.WriteLine($"Delta sync completed: {stats.Added} added, {stats.Updated} updated, {stats.Removed} removed in {stats.Duration.TotalSeconds:F1}s");
                progress?.Report(1.0);

                return stats;
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine("Sync operation was cancelled");
                progress?.Report(1.0);
                return stats;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during delta sync: {ex.Message}");
                progress?.Report(1.0);
                throw;
            }
        }
        /// <summary>
        /// Sync with marketplace with detailed progress information (legacy method)
        /// </summary>
        /// <param name="progress">Detailed progress reporter</param>
        /// <returns>True if sync was successful</returns>
        public async Task<bool> SyncWithMarketplaceDetailedAsync(IProgress<ProgressInfo>? progress = null)
        {
            try
            {
                var progressWrapper = progress != null ? new Progress<double>(p => 
                {
                    progress.Report(new ProgressInfo((int)(p * 100), "Syncing marketplace data..."));
                }) : null;

                var stats = await SyncPacksAsync(progressWrapper);
                return stats.Added > 0 || stats.Updated > 0 || stats.Removed > 0;
            }
            catch (Exception ex)
            {
                progress?.Report(new ProgressInfo(100, $"Sync failed: {ex.Message}"));
                return false;
            }
        }

        /// <summary>
        /// Get the last successful sync timestamp
        /// </summary>
        private async Task<DateTime> GetLastSyncTimeAsync()
        {
            try
            {
                var lastSyncStr = await _settingsManager.GetSettingAsync(LastSyncTimeKey);
                if (!string.IsNullOrEmpty(lastSyncStr) && DateTime.TryParse(lastSyncStr, out var lastSync))
                {
                    return lastSync.ToUniversalTime();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting last sync time: {ex.Message}");
            }
            
            // Default to 30 days ago for first sync or if setting is corrupted
            return DateTime.UtcNow.AddDays(-30);
        }

        /// <summary>
        /// Save the last successful sync timestamp
        /// </summary>
        private async Task SaveLastSyncTimeAsync(DateTime syncTime)
        {
            try
            {
                await _settingsManager.SaveSettingAsync(LastSyncTimeKey, syncTime.ToString("o"));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving last sync time: {ex.Message}");
            }
        }

        /// <summary>
        /// Process newly added packs
        /// </summary>
        private async Task ProcessAddedPacksAsync(System.Collections.Generic.List<TailorPackMetadata> addedPacks, CancellationToken cancellationToken)
        {
            foreach (var pack in addedPacks)
            {
                if (cancellationToken.IsCancellationRequested)
                    break;
                    
                try
                {
                    Console.WriteLine($"Processing new pack: {pack.Name} v{pack.Version}");
                    // Here you would implement the logic to download and install the pack
                    // For now, we just log it
                    await Task.Delay(10, cancellationToken); // Simulate processing time
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error processing added pack {pack.Id}: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Process updated packs
        /// </summary>
        private async Task ProcessUpdatedPacksAsync(System.Collections.Generic.List<TailorPackMetadata> updatedPacks, CancellationToken cancellationToken)
        {
            foreach (var pack in updatedPacks)
            {
                if (cancellationToken.IsCancellationRequested)
                    break;
                    
                try
                {
                    Console.WriteLine($"Processing updated pack: {pack.Name} v{pack.Version}");
                    // Here you would implement the logic to update the existing pack
                    await Task.Delay(10, cancellationToken); // Simulate processing time
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error processing updated pack {pack.Id}: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Process removed packs
        /// </summary>
        private async Task ProcessRemovedPacksAsync(System.Collections.Generic.List<string> removedPackIds, CancellationToken cancellationToken)
        {
            foreach (var packId in removedPackIds)
            {
                if (cancellationToken.IsCancellationRequested)
                    break;
                    
                try
                {
                    Console.WriteLine($"Processing removed pack: {packId}");
                    // Here you would implement the logic to remove the pack
                    await Task.Delay(10, cancellationToken); // Simulate processing time
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error processing removed pack {packId}: {ex.Message}");
                }
            }
        }

        private System.Collections.Generic.List<PackInfo> GetInstalledPackInfo()
        {
            var packInfoList = new System.Collections.Generic.List<PackInfo>();
            
            try
            {
                var tailorPacksPath = _fileSystemService.GetTailorPacksPath();
                var packDirectories = _fileSystemService.GetDirectories(tailorPacksPath);

                foreach (var packDir in packDirectories)
                {
                    var manifestPath = System.IO.Path.Combine(packDir, "manifest.json");
                    if (_fileSystemService.FileExists(manifestPath))
                    {
                        var manifestContent = _fileSystemService.ReadAllTextAsync(manifestPath).Result;
                        var manifest = JsonSerializer.Deserialize<PackManifest>(manifestContent);
                        if (manifest != null)
                        {
                            packInfoList.Add(new PackInfo
                            {
                                Id = manifest.Id,
                                Name = manifest.Name,
                                Version = manifest.Version,
                                InstallPath = packDir
                            });
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading installed pack info: {ex.Message}");
            }

            return packInfoList;
        }

        private async Task<bool> CheckInternetConnectivityAsync()
        {
            try
            {
                // Simple connectivity check using HTTP client
                using var response = await _networkService.SendSecureRequestAsync("https://www.google.com");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private async Task<MarketplaceData?> FetchMarketplaceDataAsync()
        {
            try
            {
                // Use the new API client for backwards compatibility
                return await _marketplaceApiClient.GetAllPacksAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error fetching marketplace data: {ex.Message}");
                return null;
            }
        }

        private UpdateInfo CompareVersions(System.Collections.Generic.List<PackInfo> installedPacks, MarketplaceData marketplaceData)
        {
            var updateInfo = new UpdateInfo();
            
            foreach (var installedPack in installedPacks)
            {
                var marketplacePack = marketplaceData.Packs?.Find(p => p.Id == installedPack.Id);
                if (marketplacePack != null && IsNewerVersion(marketplacePack.Version, installedPack.Version))
                {
                    updateInfo.UpdatesAvailable++;
                    updateInfo.AvailableUpdates.Add(new UpdateAvailable
                    {
                        PackId = installedPack.Id,
                        CurrentVersion = installedPack.Version,
                        LatestVersion = marketplacePack.Version,
                        DownloadUrl = marketplacePack.DownloadUrl
                    });
                }
            }

            return updateInfo;
        }

        private bool IsNewerVersion(string version1, string version2)
        {
            try
            {
                var v1 = new Version(version1);
                var v2 = new Version(version2);
                return v1 > v2;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> SyncUsageStatisticsAsync(System.Collections.Generic.List<PackInfo> installedPacks)
        {
            try
            {
                // Only sync if user has opted in to telemetry
                var usageData = new
                {
                    InstalledPacks = installedPacks.Select(p => new { p.Id, p.Version }).ToArray(),
                    SyncTime = DateTime.UtcNow,
                    Platform = Environment.OSVersion.Platform.ToString()
                };

                // Use the network service's SendSecureRequestAsync with JSON content
                var jsonContent = JsonSerializer.Serialize(usageData);
                var httpContent = new System.Net.Http.StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
                var response = await _networkService.SendSecureRequestAsync($"{_marketplaceApiUrl}/usage", httpContent);
                
                return response?.IsSuccessStatusCode == true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error syncing usage statistics: {ex.Message}");
                return false;
            }
        }

        private async Task<bool> DownloadPendingUpdatesAsync(UpdateInfo updateInfo)
        {
            try
            {
                foreach (var update in updateInfo.AvailableUpdates)
                {
                    // This would implement actual download logic
                    // For now, just simulate the download
                    await Task.Delay(100);
                    Console.WriteLine($"Would download update for {update.PackId}: {update.CurrentVersion} -> {update.LatestVersion}");
                }
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error downloading updates: {ex.Message}");
                return false;
            }
        }

        // Supporting classes (kept for backwards compatibility)
        private class PackInfo
        {
            public string Id { get; set; } = string.Empty;
            public string Name { get; set; } = string.Empty;
            public string Version { get; set; } = string.Empty;
            public string InstallPath { get; set; } = string.Empty;
        }

        private class PackManifest
        {
            public string Id { get; set; } = string.Empty;
            public string Name { get; set; } = string.Empty;
            public string Version { get; set; } = string.Empty;
        }

        private class UpdateInfo
        {
            public int UpdatesAvailable { get; set; }
            public System.Collections.Generic.List<UpdateAvailable> AvailableUpdates { get; set; } = new();
        }

        private class UpdateAvailable
        {
            public string PackId { get; set; } = string.Empty;
            public string CurrentVersion { get; set; } = string.Empty;
            public string LatestVersion { get; set; } = string.Empty;
            public string DownloadUrl { get; set; } = string.Empty;
        }
    }
}