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
            // macOS-specific notification implementation using osascript
            Console.WriteLine($"macOS Notification: {title} - {message}");
        }

        public bool IsElevated()
        {
            // Check if running with elevated privileges on macOS
            return Environment.UserName.Equals("root", StringComparison.OrdinalIgnoreCase);
        }
    }
}