using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class LinuxPlatformService : IPlatformService
    {
        public string GetPlatformName() => "Linux";

        public string GetAppDataPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), 
                ".config", "westfall-assistant");
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
                catch
                {
                    // notify-send not available, fallback already printed to console
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error showing Linux notification: {ex.Message}");
            }
        }

        public bool IsElevated()
        {
            // Check if running with elevated privileges on Linux
            return Environment.UserName.Equals("root", StringComparison.OrdinalIgnoreCase);
        }
    }
}