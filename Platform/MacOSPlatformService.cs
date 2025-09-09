using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class MacOSPlatformService : IPlatformService
    {
        public string GetPlatformName() => "macOS";

        public string GetAppDataPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), 
                "Library", "Application Support", "WestfallAssistant");
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
                catch
                {
                    // osascript not available, fallback already printed to console
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing macOS notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            // Check if running with elevated privileges on macOS
            return Environment.UserName.Equals("root", StringComparison.OrdinalIgnoreCase);
        }
    }
}