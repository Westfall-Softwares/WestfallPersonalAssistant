using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class MacOSPlatformService : IPlatformService
    {
        public string GetPlatformName() => "macOS";

        public string GetAppDataPath()
        {
            try
            {
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), 
                    "Library", "Application Support", "WestfallAssistant");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not get standard app support path: {ex.Message}");
                // Fallback to user profile
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "WestfallAssistant");
            }
        }

        public void ShowNotification(string title, string message)
        {
            try
            {
                // Use osascript for macOS notifications
                var escapedTitle = title.Replace("\"", "\\\"");
                var escapedMessage = message.Replace("\"", "\\\"");
                
                Console.WriteLine($"🍎 macOS Notification: {title}");
                Console.WriteLine($"   {message}");
                
                // Try to use osascript for native macOS notifications
                if (SupportsNativeNotifications())
                {
                    try
                    {
                        var script = $"display notification \"{escapedMessage}\" with title \"{escapedTitle}\"";
                        var processInfo = new System.Diagnostics.ProcessStartInfo
                        {
                            FileName = "osascript",
                            Arguments = $"-e \"{script}\"",
                            UseShellExecute = false,
                            CreateNoWindow = true
                        };
                        
                        var process = System.Diagnostics.Process.Start(processInfo);
                        process?.WaitForExit(1000); // Wait max 1 second
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Warning: osascript failed: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing macOS notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            try
            {
                // Check if running with elevated privileges on macOS
                return Environment.UserName.Equals("root", StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not determine elevation status: {ex.Message}");
                return false;
            }
        }

        public bool SupportsNativeNotifications()
        {
            try
            {
                // Check if osascript is available
                var processInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "which",
                    Arguments = "osascript",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true
                };
                
                using var process = System.Diagnostics.Process.Start(processInfo);
                process?.WaitForExit(1000);
                return process?.ExitCode == 0;
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
                // macOS generally supports all file system features we need
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