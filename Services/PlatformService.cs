using System;
using System.Runtime.InteropServices;
using WestfallPersonalAssistant.Platform;

namespace WestfallPersonalAssistant.Services
{
    public class PlatformService
    {
        private static IPlatformService? _instance;
        
        public static IPlatformService Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = CreatePlatformService();
                }
                return _instance;
            }
        }
        
        /// <summary>
        /// Gets the current platform name for display purposes
        /// </summary>
        public static string CurrentPlatformName => GetPlatformDisplayName();
        
        /// <summary>
        /// Checks if the current platform is fully supported
        /// </summary>
        public static bool IsCurrentPlatformSupported => IsMainPlatformSupported();
        
        private static IPlatformService CreatePlatformService()
        {
            try
            {
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                {
                    return new WindowsPlatformService();
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                {
                    return new MacOSPlatformService();
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    return new LinuxPlatformService();
                }
                else
                {
                    // Graceful fallback for unsupported platforms
                    var platformName = GetPlatformDisplayName();
                    Console.WriteLine($"Warning: Platform '{platformName}' is not fully supported. Using fallback implementation.");
                    return new FallbackPlatformService(platformName);
                }
            }
            catch (Exception ex)
            {
                // If platform detection fails entirely, use fallback
                Console.WriteLine($"Error during platform detection: {ex.Message}. Using fallback implementation.");
                return new FallbackPlatformService("Unknown");
            }
        }
        
        private static string GetPlatformDisplayName()
        {
            try
            {
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                    return "Windows";
                if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                    return "macOS";
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                    return "Linux";
                if (RuntimeInformation.IsOSPlatform(OSPlatform.FreeBSD))
                    return "FreeBSD";
                
                // Try to get OS description as fallback
                return RuntimeInformation.OSDescription;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Could not determine platform name: {ex.Message}");
                return "Unknown";
            }
        }
        
        private static bool IsMainPlatformSupported()
        {
            try
            {
                return RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ||
                       RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ||
                       RuntimeInformation.IsOSPlatform(OSPlatform.Linux);
            }
            catch
            {
                return false;
            }
        }
    }
}