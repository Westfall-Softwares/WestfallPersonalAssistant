using System;
using System.IO;

namespace WestfallPersonalAssistant.Platform
{
    public class WindowsPlatformService : IPlatformService
    {
        public string GetPlatformName() => "Windows";

        public string GetAppDataPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WestfallAssistant");
        }

        public void ShowNotification(string title, string message)
        {
            // Windows-specific notification implementation
            Console.WriteLine($"Windows Notification: {title} - {message}");
        }

        public bool IsElevated()
        {
            // Check if running as administrator on Windows
            return Environment.UserName.Equals("Administrator", StringComparison.OrdinalIgnoreCase);
        }
    }
}