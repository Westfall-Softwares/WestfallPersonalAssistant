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
                // Check if running as administrator on Windows
                var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
            }
            catch
            {
                // Fallback method
                return Environment.UserName.Equals("Administrator", StringComparison.OrdinalIgnoreCase);
            }
        }
    }
}