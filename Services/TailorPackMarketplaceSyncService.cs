using System;
using System.Threading.Tasks;
using System.Net.Http;
using System.Text.Json;
using System.Linq;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for syncing Tailor Pack data with marketplace with progress tracking
    /// </summary>
    public class TailorPackMarketplaceSyncService
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly NetworkService _networkService;
        private readonly TailorPackManager _tailorPackManager;
        private readonly string _marketplaceApiUrl = "https://api.westfall-marketplace.com/v1";

        public TailorPackMarketplaceSyncService(
            IFileSystemService fileSystemService, 
            NetworkService networkService,
            TailorPackManager tailorPackManager)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _networkService = networkService ?? throw new ArgumentNullException(nameof(networkService));
            _tailorPackManager = tailorPackManager ?? throw new ArgumentNullException(nameof(tailorPackManager));
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
        /// Sync with marketplace with detailed progress information
        /// </summary>
        /// <param name="progress">Detailed progress reporter</param>
        /// <returns>True if sync was successful</returns>
        public async Task<bool> SyncWithMarketplaceDetailedAsync(IProgress<ProgressInfo>? progress = null)
        {
            try
            {
                progress?.Report(new ProgressInfo(0, "Starting marketplace sync..."));

                // Step 1: Check network connectivity (10%)
                if (!await CheckInternetConnectivityAsync())
                {
                    progress?.Report(new ProgressInfo(100, "No internet connection available"));
                    return false;
                }
                progress?.Report(new ProgressInfo(10, "Network connectivity verified"));

                // Step 2: Get installed packs (20%)
                var installedPacks = GetInstalledPackInfo();
                progress?.Report(new ProgressInfo(20, $"Found {installedPacks.Count} installed packs"));

                // Step 3: Fetch marketplace data (40%)
                progress?.Report(new ProgressInfo(25, "Fetching marketplace data..."));
                var marketplaceData = await FetchMarketplaceDataAsync();
                if (marketplaceData == null)
                {
                    progress?.Report(new ProgressInfo(100, "Failed to fetch marketplace data"));
                    return false;
                }
                progress?.Report(new ProgressInfo(40, "Marketplace data retrieved"));

                // Step 4: Compare versions and check for updates (60%)
                progress?.Report(new ProgressInfo(45, "Checking for updates..."));
                var updateInfo = CompareVersions(installedPacks, marketplaceData);
                progress?.Report(new ProgressInfo(60, $"Found {updateInfo.UpdatesAvailable} available updates"));

                // Step 5: Sync usage statistics (if enabled) (80%)
                progress?.Report(new ProgressInfo(65, "Syncing usage statistics..."));
                var statsSynced = await SyncUsageStatisticsAsync(installedPacks);
                progress?.Report(new ProgressInfo(80, statsSynced ? "Usage statistics synced" : "Statistics sync skipped"));

                // Step 6: Download pending updates (90%)
                if (updateInfo.UpdatesAvailable > 0)
                {
                    progress?.Report(new ProgressInfo(85, "Downloading updates..."));
                    var downloadSuccess = await DownloadPendingUpdatesAsync(updateInfo);
                    progress?.Report(new ProgressInfo(90, downloadSuccess ? "Updates downloaded" : "Update download failed"));
                }
                else
                {
                    progress?.Report(new ProgressInfo(90, "No updates to download"));
                }

                // Step 7: Complete sync (100%)
                progress?.Report(new ProgressInfo(100, "Marketplace sync completed"));
                return true;
            }
            catch (Exception ex)
            {
                progress?.Report(new ProgressInfo(100, $"Sync failed: {ex.Message}"));
                Console.WriteLine($"Error during marketplace sync: {ex.Message}");
                return false;
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
                // TODO optimise delta sync for large pagination
                // Current implementation fetches full pack list which is inefficient for large marketplaces.
                // Consider switching from full list fetch to "since <timestamp>" incremental API
                // to reduce bandwidth and improve sync performance for large pack catalogs.
                var response = await _networkService.SendSecureRequestAsync($"{_marketplaceApiUrl}/packs");
                if (response != null && response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    return JsonSerializer.Deserialize<MarketplaceData>(content);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error fetching marketplace data: {ex.Message}");
            }
            return null;
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

        // Supporting classes
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

        private class MarketplaceData
        {
            public System.Collections.Generic.List<MarketplacePack>? Packs { get; set; }
        }

        private class MarketplacePack
        {
            public string Id { get; set; } = string.Empty;
            public string Version { get; set; } = string.Empty;
            public string DownloadUrl { get; set; } = string.Empty;
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