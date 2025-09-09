using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Threading;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for secure network communication services
    /// </summary>
    public interface INetworkService
    {
        Task<string> GetApiKeyAsync(string keyName);
        Task SetApiKeyAsync(string keyName, string apiKey);
        Task<HttpResponseMessage> SendSecureRequestAsync(string endpoint, HttpContent content = null, CancellationToken cancellationToken = default);
        Task<T> GetAsync<T>(string endpoint, CancellationToken cancellationToken = default);
        Task<T> PostAsync<T>(string endpoint, object data, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Secure network service implementation with proper credential management
    /// </summary>
    public class NetworkService : INetworkService, IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly ISecureStorageService _secureStorage;
        private bool _disposed = false;

        // Secure API key storage keys
        private const string DefaultApiKeyStorageKey = "network_api_key";
        private const string TelemetryApiKeyStorageKey = "telemetry_api_key";

        public NetworkService(ISecureStorageService secureStorage)
        {
            _secureStorage = secureStorage ?? throw new ArgumentNullException(nameof(secureStorage));
            
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
            
            // Set security headers
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "WestfallAssistant/1.0");
            
            Console.WriteLine("NetworkService initialized with secure configuration");
        }

        public async Task<string> GetApiKeyAsync(string keyName)
        {
            if (string.IsNullOrEmpty(keyName))
                throw new ArgumentException("Key name cannot be null or empty", nameof(keyName));

            try
            {
                var storageKey = GetStorageKeyForApiKey(keyName);
                var apiKey = _secureStorage.RetrieveSecureData(storageKey);
                
                if (string.IsNullOrEmpty(apiKey))
                {
                    Console.WriteLine($"API key not found for: {keyName}");
                    return null;
                }

                Console.WriteLine($"API key retrieved for: {keyName}");
                return apiKey;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to retrieve API key for {keyName}: {ex.Message}");
                throw new InvalidOperationException($"Failed to retrieve API key for {keyName}", ex);
            }
        }

        public async Task SetApiKeyAsync(string keyName, string apiKey)
        {
            if (string.IsNullOrEmpty(keyName))
                throw new ArgumentException("Key name cannot be null or empty", nameof(keyName));
            
            if (string.IsNullOrEmpty(apiKey))
                throw new ArgumentException("API key cannot be null or empty", nameof(apiKey));

            try
            {
                var storageKey = GetStorageKeyForApiKey(keyName);
                _secureStorage.StoreSecureData(storageKey, apiKey);
                
                Console.WriteLine($"API key stored securely for: {keyName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to store API key for {keyName}: {ex.Message}");
                throw new InvalidOperationException($"Failed to store API key for {keyName}", ex);
            }
        }

        public async Task<HttpResponseMessage> SendSecureRequestAsync(string endpoint, HttpContent content = null, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(endpoint))
                throw new ArgumentException("Endpoint cannot be null or empty", nameof(endpoint));

            try
            {
                Console.WriteLine($"Sending secure request to: {SanitizeUrl(endpoint)}");

                HttpResponseMessage response;
                if (content != null)
                {
                    response = await _httpClient.PostAsync(endpoint, content, cancellationToken);
                }
                else
                {
                    response = await _httpClient.GetAsync(endpoint, cancellationToken);
                }

                Console.WriteLine($"Request completed with status: {response.StatusCode}");
                return response;
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"ERROR: HTTP request failed for endpoint: {SanitizeUrl(endpoint)}: {ex.Message}");
                throw;
            }
            catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
            {
                Console.WriteLine($"ERROR: Request timeout for endpoint: {SanitizeUrl(endpoint)}: {ex.Message}");
                throw new TimeoutException($"Request to {SanitizeUrl(endpoint)} timed out", ex);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Unexpected error for endpoint: {SanitizeUrl(endpoint)}: {ex.Message}");
                throw;
            }
        }

        public async Task<T> GetAsync<T>(string endpoint, CancellationToken cancellationToken = default)
        {
            var response = await SendSecureRequestAsync(endpoint, null, cancellationToken);
            response.EnsureSuccessStatusCode();
            
            var content = await response.Content.ReadAsStringAsync();
            return Newtonsoft.Json.JsonConvert.DeserializeObject<T>(content);
        }

        public async Task<T> PostAsync<T>(string endpoint, object data, CancellationToken cancellationToken = default)
        {
            var json = Newtonsoft.Json.JsonConvert.SerializeObject(data);
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
            
            var response = await SendSecureRequestAsync(endpoint, content, cancellationToken);
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            return Newtonsoft.Json.JsonConvert.DeserializeObject<T>(responseContent);
        }

        private string GetStorageKeyForApiKey(string keyName)
        {
            return keyName.ToLowerInvariant() switch
            {
                "default" => DefaultApiKeyStorageKey,
                "telemetry" => TelemetryApiKeyStorageKey,
                _ => $"api_key_{keyName.ToLowerInvariant()}"
            };
        }

        private string SanitizeUrl(string url)
        {
            if (string.IsNullOrEmpty(url))
                return "[EMPTY_URL]";

            try
            {
                var uri = new Uri(url);
                return $"{uri.Scheme}://{uri.Host}{uri.AbsolutePath}";
            }
            catch
            {
                return "[INVALID_URL]";
            }
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _httpClient?.Dispose();
                Console.WriteLine("NetworkService disposed");
                _disposed = true;
            }
        }
    }
}