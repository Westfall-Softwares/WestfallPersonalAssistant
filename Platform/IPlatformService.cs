namespace WestfallPersonalAssistant.Platform
{
    public interface IPlatformService
    {
        string GetPlatformName();
        string GetAppDataPath();
        void ShowNotification(string title, string message);
        bool IsElevated();
        
        /// <summary>
        /// Checks if native notifications are supported on this platform
        /// </summary>
        bool SupportsNativeNotifications();
        
        /// <summary>
        /// Checks if the platform-specific file system features are available
        /// </summary>
        bool SupportsFileSystemFeatures();
        
        /// <summary>
        /// Gets platform-specific information and capabilities
        /// </summary>
        PlatformCapabilities GetCapabilities();
    }
    
    /// <summary>
    /// Represents platform-specific capabilities
    /// </summary>
    public class PlatformCapabilities
    {
        public bool HasNativeNotifications { get; set; }
        public bool HasFileSystemWatcher { get; set; }
        public bool HasSystemTray { get; set; }
        public bool HasElevationDetection { get; set; }
        public string PlatformVersion { get; set; } = string.Empty;
        public string[] SupportedFeatures { get; set; } = Array.Empty<string>();
    }
}