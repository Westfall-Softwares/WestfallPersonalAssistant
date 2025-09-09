using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Implementation of marketplace API client with delta sync support
    /// </summary>
    public class MarketplaceApiClient : IMarketplaceApiClient
    {
        private readonly INetworkService _networkService;
        private readonly string _baseUrl;

        public MarketplaceApiClient(INetworkService networkService, string baseUrl = "https://api.westfall-marketplace.com/v1")
        {
            _networkService = networkService ?? throw new ArgumentNullException(nameof(networkService));
            _baseUrl = baseUrl ?? throw new ArgumentNullException(nameof(baseUrl));
        }

        /// <summary>
        /// Get packs that have changed since the specified timestamp
        /// </summary>
        public async Task<MarketplaceSyncResult> GetPacksChangedSinceAsync(
            DateTime lastSyncTime, 
            string? continuationToken = null,
            CancellationToken cancellationToken = default)
        {
            try
            {
                // Build query parameters
                var queryParams = new List<string>
                {
                    $"since={lastSyncTime:yyyy-MM-ddTHH:mm:ssZ}",
                    "format=delta"
                };

                if (!string.IsNullOrEmpty(continuationToken))
                {
                    queryParams.Add($"continuation={Uri.EscapeDataString(continuationToken)}");
                }

                var queryString = string.Join("&", queryParams);
                var endpoint = $"{_baseUrl}/packs/delta?{queryString}";

                var response = await _networkService.SendSecureRequestAsync(endpoint, null, cancellationToken);
                
                if (!response.IsSuccessStatusCode)
                {
                    throw new InvalidOperationException($"Marketplace API returned {response.StatusCode}: {response.ReasonPhrase}");
                }

                var content = await response.Content.ReadAsStringAsync();
                var apiResponse = JsonSerializer.Deserialize<DeltaSyncResponse>(content, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                if (apiResponse == null)
                {
                    throw new InvalidOperationException("Failed to deserialize marketplace response");
                }

                return new MarketplaceSyncResult
                {
                    AddedPacks = apiResponse.Added ?? new List<TailorPackMetadata>(),
                    UpdatedPacks = apiResponse.Updated ?? new List<TailorPackMetadata>(),
                    RemovedPackIds = apiResponse.Removed ?? new List<string>(),
                    ContinuationToken = apiResponse.ContinuationToken,
                    EstimatedTotalChanges = apiResponse.EstimatedTotal,
                    CurrentPage = apiResponse.CurrentPage
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting delta sync data: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Get all packs (legacy method for compatibility)
        /// </summary>
        public async Task<MarketplaceData?> GetAllPacksAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                var endpoint = $"{_baseUrl}/packs";
                var response = await _networkService.SendSecureRequestAsync(endpoint, null, cancellationToken);
                
                if (!response.IsSuccessStatusCode)
                {
                    return null;
                }

                var content = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<MarketplaceData>(content, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting all packs: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Internal response structure for delta sync API
        /// </summary>
        private class DeltaSyncResponse
        {
            public List<TailorPackMetadata>? Added { get; set; }
            public List<TailorPackMetadata>? Updated { get; set; }
            public List<string>? Removed { get; set; }
            public string? ContinuationToken { get; set; }
            public int? EstimatedTotal { get; set; }
            public int CurrentPage { get; set; } = 1;
        }
    }

    /// <summary>
    /// Mock implementation for testing and development
    /// </summary>
    public class MockMarketplaceApiClient : IMarketplaceApiClient
    {
        private readonly List<TailorPackMetadata> _allPacks;
        private readonly Random _random;

        public MockMarketplaceApiClient()
        {
            _random = new Random();
            _allPacks = GenerateMockPacks();
        }

        public async Task<MarketplaceSyncResult> GetPacksChangedSinceAsync(
            DateTime lastSyncTime, 
            string? continuationToken = null,
            CancellationToken cancellationToken = default)
        {
            // Simulate network delay
            await Task.Delay(100, cancellationToken);

            // Simulate some changes based on time
            var result = new MarketplaceSyncResult();
            
            // Add some mock changes
            if (DateTime.UtcNow.Subtract(lastSyncTime).TotalDays > 7)
            {
                // Simulate more changes for older sync times
                result.AddedPacks.Add(CreateMockPack("new-pack-" + _random.Next(1000, 9999)));
                result.UpdatedPacks.Add(_allPacks[_random.Next(_allPacks.Count)]);
            }
            else if (DateTime.UtcNow.Subtract(lastSyncTime).TotalDays > 1)
            {
                // Some changes for recent syncs
                if (_random.Next(2) == 0)
                {
                    result.UpdatedPacks.Add(_allPacks[_random.Next(_allPacks.Count)]);
                }
            }

            // Simulate pagination
            if (continuationToken == null && result.AddedPacks.Count + result.UpdatedPacks.Count > 5)
            {
                result.ContinuationToken = "mock-token-" + Guid.NewGuid().ToString("N")[..8];
            }

            result.EstimatedTotalChanges = result.AddedPacks.Count + result.UpdatedPacks.Count + result.RemovedPackIds.Count;

            return result;
        }

        public async Task<MarketplaceData?> GetAllPacksAsync(CancellationToken cancellationToken = default)
        {
            // Simulate network delay
            await Task.Delay(200, cancellationToken);

            return new MarketplaceData
            {
                Packs = _allPacks.ConvertAll(pack => new MarketplacePack
                {
                    Id = pack.Id,
                    Version = pack.Version,
                    DownloadUrl = pack.DownloadUrl
                })
            };
        }

        private List<TailorPackMetadata> GenerateMockPacks()
        {
            return new List<TailorPackMetadata>
            {
                CreateMockPack("marketing-essentials", "Marketing Essentials", "1.2.0"),
                CreateMockPack("analytics-pro", "Analytics Pro", "2.1.0"),
                CreateMockPack("project-management", "Project Management Suite", "1.0.3"),
                CreateMockPack("crm-basic", "CRM Basic", "1.1.0"),
                CreateMockPack("financial-tools", "Financial Tools", "1.5.2")
            };
        }

        private TailorPackMetadata CreateMockPack(string id, string? name = null, string? version = null)
        {
            return new TailorPackMetadata
            {
                Id = id,
                Name = name ?? $"Mock Pack {id}",
                Version = version ?? "1.0.0",
                Description = $"Mock description for {name ?? id}",
                DownloadUrl = $"https://marketplace.example.com/downloads/{id}.zip",
                LastModified = DateTime.UtcNow.AddDays(-_random.Next(0, 30)),
                SizeBytes = _random.Next(1024 * 100, 1024 * 1024 * 10), // 100KB to 10MB
                Author = "Mock Author",
                Tags = new List<string> { "productivity", "business" }
            };
        }
    }
}