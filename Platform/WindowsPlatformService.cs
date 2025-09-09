using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class WindowsPlatformService : IPlatformService
    {
        public string GetPlatformName() => "Windows";

        public string GetAppDataPath()
        {
            try
            {
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WestfallAssistant");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not get standard app data path: {ex.Message}");
                // Fallback to user profile
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "WestfallAssistant");
            }
        }

        public void ShowNotification(string title, string message)
        {
            try
            {
                // Use Windows Toast Notifications for better user experience
                // For now, fallback to console output
                Console.WriteLine($"🔔 Windows Notification: {title}");
                Console.WriteLine($"   {message}");
                
                // TODO: In future, implement Windows.UI.Notifications.ToastNotification
                // for proper Windows 10/11 toast notifications
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing Windows notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            try
            {
#if WINDOWS
                // Check if running as administrator on Windows
                var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
#else
                // Fallback method for cross-platform compilation
                return Environment.UserName.Equals("Administrator", StringComparison.OrdinalIgnoreCase);
#endif
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not determine elevation status: {ex.Message}");
                // Fallback method
                return Environment.UserName.Equals("Administrator", StringComparison.OrdinalIgnoreCase);
            }
        }

        public bool SupportsNativeNotifications()
        {
            try
            {
                // Windows 10+ supports toast notifications
                var version = Environment.OSVersion.Version;
                return version.Major >= 10;
            }
            catch
            {
                return false;
            }
        }

        public bool SupportsFileSystemFeatures()
        {
            try
            {
                // Windows generally supports all file system features we need
                return true;
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
                HasNativeNotifications = SupportsNativeNotifications(),
                HasFileSystemWatcher = true,
                HasSystemTray = true,
                HasElevationDetection = true,
                PlatformVersion = Environment.OSVersion.VersionString,
                SupportedFeatures = new[] { "notifications", "file_watcher", "system_tray", "elevation_check", "keyboard_shortcuts" }
            };
        }
    }
}