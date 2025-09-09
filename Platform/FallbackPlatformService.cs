using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    /// <summary>
    /// Fallback platform service for unsupported platforms.
    /// Provides basic functionality with minimal platform assumptions.
    /// </summary>
    public class FallbackPlatformService : IPlatformService
    {
        private readonly string _platformName;

        public FallbackPlatformService(string platformName = "Unknown")
        {
            _platformName = platformName;
        }

        public string GetPlatformName() => _platformName;

        public string GetAppDataPath()
        {
            try
            {
                // Try to use standard user profile directory
                var userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                if (!string.IsNullOrEmpty(userProfile))
                {
                    return Path.Combine(userProfile, ".westfall-assistant");
                }
                
                // Fallback to current directory if user profile is not available
                return Path.Combine(Environment.CurrentDirectory, "data");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not determine app data path: {ex.Message}");
                // Ultimate fallback - use current directory
                return Path.Combine(".", "data");
            }
        }

        public void ShowNotification(string title, string message)
        {
            try
            {
                // Simple console fallback for notifications
                Console.WriteLine($"📢 Notification: {title}");
                Console.WriteLine($"   {message}");
                
                // Attempt to write to a log file as an additional fallback
                try
                {
                    var logPath = Path.Combine(GetAppDataPath(), "notifications.log");
                    Directory.CreateDirectory(Path.GetDirectoryName(logPath)!);
                    
                    var logEntry = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {title}: {message}{Environment.NewLine}";
                    File.AppendAllText(logPath, logEntry);
                }
                catch
                {
                    // Ignore logging errors - console output is the primary fallback
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            try
            {
                // Basic check - assume not elevated unless we can determine otherwise
                // This is safer than assuming elevated privileges
                var userName = Environment.UserName;
                return userName.Equals("root", StringComparison.OrdinalIgnoreCase) ||
                       userName.Equals("administrator", StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not determine elevation status: {ex.Message}");
                // Default to not elevated for security
                return false;
            }
        }

        public bool SupportsNativeNotifications()
        {
            // Fallback service doesn't support native notifications
            return false;
        }

        public bool SupportsFileSystemFeatures()
        {
            try
            {
                // Test basic file system operations
                var testPath = GetAppDataPath();
                Directory.CreateDirectory(testPath);
                return Directory.Exists(testPath);
            }
            catch
            {
                return false;
            }
        }

        public PlatformCapabilities GetCapabilities()
        {
            return new PlatformCapabilities
            {
                HasNativeNotifications = false,
                HasFileSystemWatcher = false,
                HasSystemTray = false,
                HasElevationDetection = true,
                PlatformVersion = Environment.OSVersion.VersionString,
                SupportedFeatures = new[] { "basic_file_operations", "console_notifications" }
            };
        }
    }
}