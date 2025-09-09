using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class LinuxPlatformService : IPlatformService
    {
        public string GetPlatformName() => "Linux";

        public string GetAppDataPath()
        {
            try
            {
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), 
                    ".config", "westfall-assistant");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Could not get standard config path: {ex.Message}");
                // Fallback to home directory
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "westfall-assistant");
            }
        }

        public void ShowNotification(string title, string message)
        {
            try
            {
                // Use notify-send for Linux desktop notifications
                var escapedTitle = title.Replace("\"", "\\\"");
                var escapedMessage = message.Replace("\"", "\\\"");
                
                Console.WriteLine($"🐧 Linux Notification: {title}");
                Console.WriteLine($"   {message}");
                
                // Try to use notify-send if available
                if (SupportsNativeNotifications())
                {
                    try
                    {
                        var processInfo = new System.Diagnostics.ProcessStartInfo
                        {
                            FileName = "notify-send",
                            Arguments = $"\"{escapedTitle}\" \"{escapedMessage}\"",
                            UseShellExecute = false,
                            CreateNoWindow = true
                        };
                        
                        var process = System.Diagnostics.Process.Start(processInfo);
                        process?.WaitForExit(1000); // Wait max 1 second
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Warning: notify-send failed: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing Linux notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            try
            {
                // Check if running with elevated privileges on Linux
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
                // Check if notify-send is available
                var processInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "which",
                    Arguments = "notify-send",
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
                // Linux generally supports all file system features we need
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
                HasSystemTray = CheckSystemTraySupport(),
                HasElevationDetection = true,
                PlatformVersion = Environment.OSVersion.VersionString,
                SupportedFeatures = new[] { "notifications", "file_watcher", "elevation_check", "command_line" }
            };
        }

        private bool CheckSystemTraySupport()
        {
            try
            {
                // Check if we're in a desktop environment that supports system tray
                var desktop = Environment.GetEnvironmentVariable("XDG_CURRENT_DESKTOP");
                return !string.IsNullOrEmpty(desktop);
            }
            catch
            {
                return false;
            }
        }
    }
}