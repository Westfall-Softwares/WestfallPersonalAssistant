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
        
        private static IPlatformService CreatePlatformService()
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
                throw new PlatformNotSupportedException("Unsupported platform");
            }
        }
    }
}