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
            // Linux-specific notification implementation using notify-send
            Console.WriteLine($"Linux Notification: {title} - {message}");
        }

        public bool IsElevated()
        {
            // Check if running with elevated privileges on Linux
            return Environment.UserName.Equals("root", StringComparison.OrdinalIgnoreCase);
        }
    }
}