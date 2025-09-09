using System;
using Xunit;
using WestfallPersonalAssistant.Services;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;

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
}