using System;
using Xunit;
using WestfallPersonalAssistant.Services;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;
using System.IO;

namespace WestfallPersonalAssistant.Tests
{
    public class AccessibilityServiceTests
    {
        [Fact]
        public void AccessibilityService_ShouldInitializeWithDefaults()
        {
            // Arrange
            var mockSettingsManager = new MockSettingsManager();
            
            // Act
            var service = new AccessibilityService(mockSettingsManager);
            
            // Assert
            Assert.False(service.IsHighContrastMode);
            Assert.Equal(1.0, service.TextScalingFactor);
            Assert.False(service.ReduceMotion);
            Assert.False(service.ScreenReaderMode);
            Assert.True(service.ShowFocusIndicators);
            Assert.True(service.EnhancedKeyboardNavigation);
            Assert.Equal(WestfallPersonalAssistant.Models.ColorBlindnessType.None, service.ColorBlindnessAccommodation);
        }
        
        [Fact]
        public void AccessibilityService_ShouldValidateTextScalingFactor()
        {
            // Arrange
            var mockSettingsManager = new MockSettingsManager();
            var service = new AccessibilityService(mockSettingsManager);
            
            // Act & Assert - Should clamp to valid range
            service.TextScalingFactor = 0.5; // Below minimum
            Assert.Equal(0.8, service.TextScalingFactor);
            
            service.TextScalingFactor = 3.0; // Above maximum
            Assert.Equal(2.0, service.TextScalingFactor);
            
            service.TextScalingFactor = 1.5; // Valid value
            Assert.Equal(1.5, service.TextScalingFactor);
        }
        
        [Fact]
        public void AccessibilityService_ShouldTriggerPropertyChangedEvents()
        {
            // Arrange
            var mockSettingsManager = new MockSettingsManager();
            var service = new AccessibilityService(mockSettingsManager);
            var propertyChangedFired = false;
            
            service.PropertyChanged += (s, e) => {
                if (e.PropertyName == nameof(service.IsHighContrastMode))
                    propertyChangedFired = true;
            };
            
            // Act
            service.IsHighContrastMode = true;
            
            // Assert
            Assert.True(propertyChangedFired);
        }
    }
    
    public class InputValidationServiceTests
    {
        private readonly InputValidationService _service = new();
        
        [Theory]
        [InlineData("test@example.com", true)]
        [InlineData("invalid-email", false)]
        [InlineData("", false)]
        public void ValidateEmail_ShouldReturnCorrectResults(string email, bool expectedIsValid)
        {
            // Act
            var result = _service.ValidateEmail(email);
            
            // Assert
            Assert.Equal(expectedIsValid, result.IsValid);
        }
        
        [Theory]
        [InlineData("(555) 123-4567", true)]
        [InlineData("555-123-4567", true)]
        [InlineData("5551234567", true)]
        [InlineData("invalid", false)]
        [InlineData("", false)]
        public void ValidatePhoneNumber_ShouldReturnCorrectResults(string phoneNumber, bool expectedIsValid)
        {
            // Act
            var result = _service.ValidatePhoneNumber(phoneNumber);
            
            // Assert
            Assert.Equal(expectedIsValid, result.IsValid);
        }
        
        [Fact]
        public void SanitizeHtml_ShouldEscapeDangerousContent()
        {
            // Arrange
            var input = "<script>alert('xss')</script>";
            
            // Act
            var result = _service.SanitizeHtml(input);
            
            // Assert
            Assert.DoesNotContain("<script>", result);
            // HtmlSanitizer removes dangerous content entirely, which is safer than escaping
            Assert.Equal(string.Empty, result.Trim());
        }
        
        [Fact]
        public void PreventXss_ShouldRemoveDangerousPatterns()
        {
            // Arrange
            var input = "Hello <script>alert('xss')</script> World javascript:void(0)";
            
            // Act
            var result = _service.PreventXss(input);
            
            // Assert
            Assert.DoesNotContain("<script>", result);
            Assert.DoesNotContain("javascript:", result);
        }
    }
    
    // Mock implementations for testing
    public class MockSettingsManager : ISettingsManager
    {
        private WestfallPersonalAssistant.Models.ApplicationSettings _settings = new();
        
        public WestfallPersonalAssistant.Models.ApplicationSettings GetCurrentSettings() => _settings;
        public Task<WestfallPersonalAssistant.Models.ApplicationSettings> LoadSettingsAsync() => Task.FromResult(_settings);
        public Task SaveSettingsAsync(WestfallPersonalAssistant.Models.ApplicationSettings settings) { _settings = settings; return Task.CompletedTask; }
        public Task UpdateSettingAsync<T>(string key, T value) => Task.CompletedTask;
        public Task ResetSettingsAsync() => Task.CompletedTask;
        public bool SettingsExist() => true;
        public event EventHandler<WestfallPersonalAssistant.Models.ApplicationSettings>? SettingsChanged;
    }
    
    public class MockFileSystemService : IFileSystemService
    {
        private readonly Dictionary<string, string> _files = new();
        private readonly HashSet<string> _directories = new();
        
        public string GetAppDataPath() => "/tmp/test-app";
        public string GetDocumentsPath() => "/tmp/documents";
        public bool FileExists(string path) => _files.ContainsKey(path);
        public bool DirectoryExists(string path) => _directories.Contains(path);
        public void CreateDirectory(string path) => _directories.Add(path);
        public Task<string> ReadAllTextAsync(string path) => Task.FromResult(_files.GetValueOrDefault(path, ""));
        public Task WriteAllTextAsync(string path, string content) { _files[path] = content; return Task.CompletedTask; }
        public void DeleteFile(string path) => _files.Remove(path);
        public void DeleteDirectory(string path, bool recursive = true) => _directories.Remove(path);
        public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false) => _files.Keys.ToArray();
        public string[] GetDirectories(string path) => _directories.ToArray();
        public long GetFileSize(string path) => _files.GetValueOrDefault(path, "").Length;
        public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false) => _files[destinationPath] = _files[sourcePath];
        public void MoveFile(string sourcePath, string destinationPath) { _files[destinationPath] = _files[sourcePath]; _files.Remove(sourcePath); }
        public string GetTailorPacksPath() => "/tmp/packs";
        public string GetSettingsPath() => "/tmp/settings.json";
        public string GetLogsPath() => "/tmp/logs";
    }
    
    // Test classes for new functionality
    public class ResultPatternTests
    {
        [Fact]
        public void Result_Success_ShouldReturnSuccessfulResult()
        {
            // Arrange & Act
            var result = Result<string>.Success("test value");
            
            // Assert
            Assert.True(result.IsSuccess);
            Assert.Equal("test value", result.Value);
            Assert.Equal(string.Empty, result.ErrorMessage);
            Assert.Null(result.Exception);
        }
        
        [Fact]
        public void Result_Failure_ShouldReturnFailedResult()
        {
            // Arrange & Act
            var result = Result<string>.Failure("error message");
            
            // Assert
            Assert.False(result.IsSuccess);
            Assert.Null(result.Value);
            Assert.Equal("error message", result.ErrorMessage);
            Assert.Null(result.Exception);
        }
        
        [Fact]
        public async Task ExceptionHandler_TryExecuteAsync_ShouldHandleExceptions()
        {
            // Arrange
            Func<Task<string>> operation = () => throw new ArgumentException("test exception");
            
            // Act
            var result = await ExceptionHandler.TryExecuteAsync(operation, "User error message");
            
            // Assert
            Assert.False(result.IsSuccess);
            Assert.Equal("Invalid input provided. Please check your data.", result.ErrorMessage);
            Assert.NotNull(result.Exception);
        }
    }
    
    public class TailorPackSecurityTests
    {
        private readonly TailorPackSecurityService _service;
        private readonly MockSecurityLogger _securityLogger;
        private readonly InputValidationService _validationService;
        
        public TailorPackSecurityTests()
        {
            _securityLogger = new MockSecurityLogger();
            _validationService = new InputValidationService();
            _service = new TailorPackSecurityService(_securityLogger, _validationService);
        }
        
        [Fact]
        public void GetDefaultPermissions_ShouldReturnSecureDefaults()
        {
            // Act
            var permissions = _service.GetDefaultPermissions();
            
            // Assert
            Assert.False(permissions.AllowFileSystem);
            Assert.False(permissions.AllowNetwork);
            Assert.False(permissions.AllowDatabase);
            Assert.True(permissions.AllowUserInterface);
            Assert.Equal(TimeSpan.FromSeconds(30), permissions.MaxExecutionTime);
        }
        
        [Fact]
        public async Task LoadPackSecurelyAsync_WithNonExistentFile_ShouldReturnFailure()
        {
            // Arrange
            var nonExistentPath = "/tmp/nonexistent.dll";
            var permissions = _service.GetDefaultPermissions();
            
            // Act
            var result = await _service.LoadPackSecurelyAsync(nonExistentPath, permissions);
            
            // Assert
            Assert.False(result.IsSuccess);
            Assert.Equal("Pack file not found", result.ErrorMessage);
        }
        
        [Fact]
        public void ValidatePackSignature_WithOversizedFile_ShouldReturnFalse()
        {
            // Arrange
            var tempFile = Path.GetTempFileName();
            try
            {
                // Create a file larger than 10MB
                using var stream = new FileStream(tempFile, FileMode.Create);
                stream.SetLength(11 * 1024 * 1024); // 11MB
                
                // Act
                var result = _service.ValidatePackSignature(tempFile);
                
                // Assert
                Assert.False(result);
            }
            finally
            {
                if (File.Exists(tempFile))
                    File.Delete(tempFile);
            }
        }
        
        [Fact]
        public void GetLoadedPacks_WhenNoPacks_ShouldReturnEmptyList()
        {
            // Act
            var packs = _service.GetLoadedPacks();
            
            // Assert
            Assert.Empty(packs);
        }
        
        [Fact]
        public async Task ExecutePackMethodAsync_WithUnloadedPack_ShouldReturnFailure()
        {
            // Act
            var result = await _service.ExecutePackMethodAsync("nonexistent", "testMethod");
            
            // Assert
            Assert.False(result.IsSuccess);
            Assert.Equal("Pack not loaded", result.ErrorMessage);
        }
    }
    
    // Mock security logger for testing
    public class MockSecurityLogger : ISecurityLogger
    {
        public List<SecurityEvent> LoggedEvents { get; } = new();
        
        public Task LogSecurityEventAsync(SecurityEvent securityEvent)
        {
            LoggedEvents.Add(securityEvent);
            return Task.CompletedTask;
        }
        
        public Task LogAuthenticationAttemptAsync(string username, bool success, string? failureReason = null)
        {
            return Task.CompletedTask;
        }
        
        public Task LogPrivilegedOperationAsync(string operation, string user, Dictionary<string, object>? parameters = null)
        {
            return Task.CompletedTask;
        }
        
        public Task LogDataAccessAsync(string resourceType, string resourceId, string action, string user)
        {
            return Task.CompletedTask;
        }
        
        public Task LogFileOperationAsync(string filePath, string operation, string user, bool success)
        {
            return Task.CompletedTask;
        }
        
        public Task<List<SecurityEvent>> GetSecurityEventsAsync(DateTime? fromDate = null, DateTime? toDate = null, SecurityEventType? eventType = null)
        {
            return Task.FromResult(LoggedEvents);
        }
        
        public Task<List<SecurityEvent>> GetFailedLoginsAsync(TimeSpan timeRange)
        {
            return Task.FromResult(new List<SecurityEvent>());
        }
        
        public Task<List<SecurityEvent>> GetPrivilegedOperationsAsync(string? user = null, TimeSpan? timeRange = null)
        {
            return Task.FromResult(new List<SecurityEvent>());
        }
        
        public Task<bool> CheckSuspiciousActivityAsync(string user, TimeSpan timeRange)
        {
            return Task.FromResult(false);
        }
        
        public Task<int> GetFailedLoginCountAsync(string user, TimeSpan timeRange)
        {
            return Task.FromResult(0);
        }
        
        public Task RotateLogsAsync()
        {
            return Task.CompletedTask;
        }
        
        public Task PurgeOldLogsAsync(TimeSpan retentionPeriod)
        {
            return Task.CompletedTask;
        }
        
        public void SetLogLevel(SecurityLogLevel level) { }
        
        public void EnableAuditLogging(bool enabled) { }
    }
}