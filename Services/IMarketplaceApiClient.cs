using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for marketplace API client with delta sync support
    /// </summary>
    public interface IMarketplaceApiClient
    {
        /// <summary>
        /// Get packs that have changed since the specified timestamp
        /// </summary>
        /// <param name="lastSyncTime">Last successful sync timestamp</param>
        /// <param name="continuationToken">Token for pagination</param>
        /// <param name="cancellationToken">Cancellation token</param>
        /// <returns>Sync result with changed packs and pagination info</returns>
        Task<MarketplaceSyncResult> GetPacksChangedSinceAsync(
            DateTime lastSyncTime, 
            string? continuationToken = null,
            CancellationToken cancellationToken = default);

        /// <summary>
        /// Get all packs (legacy method for compatibility)
        /// </summary>
        /// <param name="cancellationToken">Cancellation token</param>
        /// <returns>All available packs</returns>
        Task<MarketplaceData?> GetAllPacksAsync(CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Result of a marketplace delta sync operation
    /// </summary>
    public class MarketplaceSyncResult
    {
        /// <summary>
        /// Newly added packs
        /// </summary>
        public List<TailorPackMetadata> AddedPacks { get; set; } = new();

        /// <summary>
        /// Updated existing packs
        /// </summary>
        public List<TailorPackMetadata> UpdatedPacks { get; set; } = new();

        /// <summary>
        /// IDs of packs that have been removed
        /// </summary>
        public List<string> RemovedPackIds { get; set; } = new();

        /// <summary>
        /// Token for getting the next page of results
        /// </summary>
        public string? ContinuationToken { get; set; }

        /// <summary>
        /// Whether there are more results available
        /// </summary>
        public bool HasMoreResults => !string.IsNullOrEmpty(ContinuationToken);

        /// <summary>
        /// Total estimated number of changed items (for progress calculation)
        /// </summary>
        public int? EstimatedTotalChanges { get; set; }

        /// <summary>
        /// Current page number (1-based)
        /// </summary>
        public int CurrentPage { get; set; } = 1;
    }

    /// <summary>
    /// Metadata for a Tailor Pack from the marketplace
    /// </summary>
    public class TailorPackMetadata
    {
        /// <summary>
        /// Unique identifier for the pack
        /// </summary>
        public string Id { get; set; } = string.Empty;

        /// <summary>
        /// Display name of the pack
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Version string
        /// </summary>
        public string Version { get; set; } = string.Empty;

        /// <summary>
        /// Description of the pack
        /// </summary>
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// Download URL for the pack
        /// </summary>
        public string DownloadUrl { get; set; } = string.Empty;

        /// <summary>
        /// When this pack was last modified
        /// </summary>
        public DateTime LastModified { get; set; }

        /// <summary>
        /// Size of the pack in bytes
        /// </summary>
        public long SizeBytes { get; set; }

        /// <summary>
        /// Author/publisher of the pack
        /// </summary>
        public string Author { get; set; } = string.Empty;

        /// <summary>
        /// Category or tags for the pack
        /// </summary>
        public List<string> Tags { get; set; } = new();
    }

    /// <summary>
    /// Legacy marketplace data structure for compatibility
    /// </summary>
    public class MarketplaceData
    {
        /// <summary>
        /// All available packs
        /// </summary>
        public List<MarketplacePack>? Packs { get; set; }
    }

    /// <summary>
    /// Legacy pack structure for compatibility
    /// </summary>
    public class MarketplacePack
    {
        public string Id { get; set; } = string.Empty;
        public string Version { get; set; } = string.Empty;
        public string DownloadUrl { get; set; } = string.Empty;
    }

    /// <summary>
    /// Statistics from a sync operation
    /// </summary>
    public class SyncStats
    {
        public int Added { get; set; }
        public int Updated { get; set; }
        public int Removed { get; set; }
        public DateTime StartTime { get; set; } = DateTime.UtcNow;
        public DateTime? EndTime { get; set; }
        public TimeSpan Duration => EndTime?.Subtract(StartTime) ?? TimeSpan.Zero;
    }
}