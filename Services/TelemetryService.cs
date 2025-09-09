using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for secure telemetry services
    /// </summary>
    public interface ITelemetryService
    {
        Task InitializeAsync();
        Task TrackEventAsync(string eventName, Dictionary<string, object> properties = null);
        Task TrackPerformanceAsync(string operationName, TimeSpan duration, Dictionary<string, object> additionalData = null);
        Task TrackExceptionAsync(Exception exception, Dictionary<string, object> context = null);
        Task FlushAsync();
        void SetUserId(string userId);
        void SetSessionId(string sessionId);
    }

    /// <summary>
    /// Secure telemetry service implementation with proper credential management
    /// </summary>
    public class TelemetryService : ITelemetryService, IDisposable
    {
        private readonly ISecureStorageService _secureStorage;
        private readonly INetworkService _networkService;
        private readonly Queue<TelemetryEvent> _eventQueue;
        private readonly object _queueLock = new object();
        
        private string _userId;
        private string _sessionId;
        private bool _disposed = false;
        private bool _initialized = false;

        // Secure storage key for telemetry API credentials
        private const string TelemetryApiKeyStorageKey = "telemetry_api_key";
        private const string TelemetryEndpointStorageKey = "telemetry_endpoint";
        
        // Default secure endpoint (should be configured by user)
        private const string DefaultTelemetryEndpoint = "https://api.westfallsoftware.com/telemetry";

        public TelemetryService(
            ISecureStorageService secureStorage, 
            INetworkService networkService)
        {
            _secureStorage = secureStorage ?? throw new ArgumentNullException(nameof(secureStorage));
            _networkService = networkService ?? throw new ArgumentNullException(nameof(networkService));
            
            _eventQueue = new Queue<TelemetryEvent>();
            _sessionId = Guid.NewGuid().ToString();
            
            Console.WriteLine("TelemetryService created with secure configuration");
        }

        public async Task InitializeAsync()
        {
            try
            {
                // Check if telemetry API key exists
                var apiKey = _secureStorage.RetrieveSecureData(TelemetryApiKeyStorageKey);
                if (string.IsNullOrEmpty(apiKey))
                {
                    Console.WriteLine("Telemetry API key not configured - telemetry disabled");
                    return;
                }

                // Verify connectivity (without sending actual data)
                var endpoint = _secureStorage.RetrieveSecureData(TelemetryEndpointStorageKey) ?? DefaultTelemetryEndpoint;
                
                _initialized = true;
                Console.WriteLine("TelemetryService initialized successfully");
                
                // Track initialization event
                await TrackEventAsync("telemetry_service_initialized", new Dictionary<string, object>
                {
                    ["session_id"] = _sessionId,
                    ["timestamp"] = DateTime.UtcNow.ToString("O")
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine("Failed to initialize telemetry service", ex);
                // Don't throw - telemetry failures shouldn't break the application
            }
        }

        public async Task TrackEventAsync(string eventName, Dictionary<string, object> properties = null)
        {
            if (!_initialized || string.IsNullOrEmpty(eventName))
                return;

            try
            {
                var telemetryEvent = new TelemetryEvent
                {
                    EventName = SanitizeEventName(eventName),
                    Properties = SanitizeProperties(properties ?? new Dictionary<string, object>()),
                    UserId = _userId,
                    SessionId = _sessionId,
                    Timestamp = DateTime.UtcNow
                };

                lock (_queueLock)
                {
                    _eventQueue.Enqueue(telemetryEvent);
                    
                    // Auto-flush if queue gets too large
                    if (_eventQueue.Count >= 50)
                    {
                        _ = Task.Run(async () => await FlushAsync());
                    }
                }

                Console.WriteLine($"Telemetry event queued: {eventName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to track event: {eventName}", ex);
                // Don't throw - telemetry failures shouldn't break the application
            }
        }

        public async Task TrackPerformanceAsync(string operationName, TimeSpan duration, Dictionary<string, object> additionalData = null)
        {
            if (!_initialized || string.IsNullOrEmpty(operationName))
                return;

            var properties = additionalData ?? new Dictionary<string, object>();
            properties["duration_ms"] = duration.TotalMilliseconds;
            properties["operation_type"] = "performance";

            await TrackEventAsync($"performance_{SanitizeEventName(operationName)}", properties);
        }

        public async Task TrackExceptionAsync(Exception exception, Dictionary<string, object> context = null)
        {
            if (!_initialized || exception == null)
                return;

            var properties = context ?? new Dictionary<string, object>();
            properties["exception_type"] = exception.GetType().Name;
            properties["exception_message"] = SanitizeExceptionMessage(exception.Message);
            properties["stack_trace_hash"] = ComputeStackTraceHash(exception.StackTrace);

            await TrackEventAsync("application_exception", properties);
        }

        public async Task FlushAsync()
        {
            if (!_initialized)
                return;

            TelemetryEvent[] eventsToSend;
            
            lock (_queueLock)
            {
                if (_eventQueue.Count == 0)
                    return;
                    
                eventsToSend = _eventQueue.ToArray();
                _eventQueue.Clear();
            }

            try
            {
                var apiKey = _secureStorage.RetrieveSecureData(TelemetryApiKeyStorageKey);
                if (string.IsNullOrEmpty(apiKey))
                {
                    Console.WriteLine("Telemetry API key not available - events discarded");
                    return;
                }

                var endpoint = _secureStorage.RetrieveSecureData(TelemetryEndpointStorageKey) ?? DefaultTelemetryEndpoint;
                
                var payload = new
                {
                    api_key = apiKey,
                    events = eventsToSend,
                    client_info = new
                    {
                        version = "1.0.0",
                        platform = Environment.OSVersion.Platform.ToString(),
                        timestamp = DateTime.UtcNow.ToString("O")
                    }
                };

                await _networkService.PostAsync<object>(endpoint, payload);
                
                Console.WriteLine($"Telemetry batch sent successfully: {eventsToSend.Length} events");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to send telemetry batch: {eventsToSend.Length} events", ex);
                
                // Re-queue events if send failed (with limit to prevent memory issues)
                lock (_queueLock)
                {
                    var totalEvents = _eventQueue.Count + eventsToSend.Length;
                    if (totalEvents <= 200) // Limit total queued events
                    {
                        foreach (var evt in eventsToSend)
                        {
                            _eventQueue.Enqueue(evt);
                        }
                    }
                }
            }
        }

        public void SetUserId(string userId)
        {
            _userId = SanitizeUserId(userId);
            Console.WriteLine("Telemetry user ID updated");
        }

        public void SetSessionId(string sessionId)
        {
            _sessionId = string.IsNullOrEmpty(sessionId) ? Guid.NewGuid().ToString() : sessionId;
            Console.WriteLine("Telemetry session ID updated");
        }

        private string SanitizeEventName(string eventName)
        {
            if (string.IsNullOrEmpty(eventName))
                return "unknown_event";
            
            // Remove potentially sensitive information and ensure safe characters
            return System.Text.RegularExpressions.Regex.Replace(eventName, @"[^a-zA-Z0-9_.-]", "_")
                .ToLowerInvariant()
                .Substring(0, Math.Min(eventName.Length, 100));
        }

        private Dictionary<string, object> SanitizeProperties(Dictionary<string, object> properties)
        {
            var sanitized = new Dictionary<string, object>();
            
            foreach (var kvp in properties)
            {
                if (string.IsNullOrEmpty(kvp.Key) || kvp.Value == null)
                    continue;
                
                var key = SanitizePropertyKey(kvp.Key);
                var value = SanitizePropertyValue(kvp.Value);
                
                if (!string.IsNullOrEmpty(key) && value != null)
                {
                    sanitized[key] = value;
                }
            }
            
            return sanitized;
        }

        private string SanitizePropertyKey(string key)
        {
            if (string.IsNullOrEmpty(key))
                return null;
                
            // Remove sensitive patterns
            var sensitivePatterns = new[] { "password", "key", "token", "secret", "credential" };
            foreach (var pattern in sensitivePatterns)
            {
                if (key.ToLowerInvariant().Contains(pattern))
                    return null;
            }
            
            return System.Text.RegularExpressions.Regex.Replace(key, @"[^a-zA-Z0-9_.-]", "_")
                .ToLowerInvariant()
                .Substring(0, Math.Min(key.Length, 50));
        }

        private object SanitizePropertyValue(object value)
        {
            if (value == null)
                return null;
                
            switch (value)
            {
                case string str:
                    return SanitizeStringValue(str);
                case int or long or float or double or decimal or bool:
                    return value;
                case DateTime dt:
                    return dt.ToString("O");
                default:
                    return SanitizeStringValue(value.ToString());
            }
        }

        private string SanitizeStringValue(string value)
        {
            if (string.IsNullOrEmpty(value))
                return value;
                
            // Remove file paths and URLs
            value = System.Text.RegularExpressions.Regex.Replace(value, @"[A-Za-z]:\\[^\s]+", "[FILE_PATH]");
            value = System.Text.RegularExpressions.Regex.Replace(value, @"/[^\s]+", "[FILE_PATH]");
            value = System.Text.RegularExpressions.Regex.Replace(value, @"https?://[^\s]+", "[URL]");
            
            // Limit length
            return value.Substring(0, Math.Min(value.Length, 500));
        }

        private string SanitizeUserId(string userId)
        {
            if (string.IsNullOrEmpty(userId))
                return null;
                
            // Hash the user ID for privacy
            using (var sha256 = System.Security.Cryptography.SHA256.Create())
            {
                var hash = sha256.ComputeHash(System.Text.Encoding.UTF8.GetBytes(userId));
                return Convert.ToBase64String(hash).Substring(0, 16);
            }
        }

        private string SanitizeExceptionMessage(string message)
        {
            if (string.IsNullOrEmpty(message))
                return "No message";
                
            // Remove file paths and other potentially sensitive information
            message = System.Text.RegularExpressions.Regex.Replace(message, @"[A-Za-z]:\\[^\s]+", "[FILE_PATH]");
            message = System.Text.RegularExpressions.Regex.Replace(message, @"/[^\s]+", "[FILE_PATH]");
            
            return message.Substring(0, Math.Min(message.Length, 200));
        }

        private string ComputeStackTraceHash(string stackTrace)
        {
            if (string.IsNullOrEmpty(stackTrace))
                return "no_stack_trace";
                
            using (var sha256 = System.Security.Cryptography.SHA256.Create())
            {
                var hash = sha256.ComputeHash(System.Text.Encoding.UTF8.GetBytes(stackTrace));
                return Convert.ToBase64String(hash).Substring(0, 16);
            }
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                // Flush any remaining events
                try
                {
                    FlushAsync().Wait(TimeSpan.FromSeconds(5));
                }
                catch
                {
                    // Best effort flush on dispose
                }
                
                Console.WriteLine("TelemetryService disposed");
                _disposed = true;
            }
        }

        private class TelemetryEvent
        {
            public string EventName { get; set; }
            public Dictionary<string, object> Properties { get; set; }
            public string UserId { get; set; }
            public string SessionId { get; set; }
            public DateTime Timestamp { get; set; }
        }
    }
}