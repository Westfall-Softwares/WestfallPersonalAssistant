using System;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.PlatformTest
{
    class PlatformTestProgram
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Westfall Assistant Platform Compatibility Test ===");
            Console.WriteLine();
            
            try
            {
                // Test platform service creation
                Console.WriteLine("1. Testing Platform Service Creation...");
                var platformService = PlatformService.Instance;
                Console.WriteLine($"✓ Platform Service Created Successfully");
                Console.WriteLine();
                
                // Test platform detection
                Console.WriteLine("2. Testing Platform Detection...");
                Console.WriteLine($"Current Platform: {PlatformService.CurrentPlatformName}");
                Console.WriteLine($"Platform Supported: {PlatformService.IsCurrentPlatformSupported}");
                Console.WriteLine($"Service Platform Name: {platformService.GetPlatformName()}");
                Console.WriteLine();
                
                // Test app data path
                Console.WriteLine("3. Testing App Data Path...");
                var appDataPath = platformService.GetAppDataPath();
                Console.WriteLine($"App Data Path: {appDataPath}");
                Console.WriteLine();
                
                // Test capabilities
                Console.WriteLine("4. Testing Platform Capabilities...");
                var capabilities = platformService.GetCapabilities();
                Console.WriteLine($"Platform Version: {capabilities.PlatformVersion}");
                Console.WriteLine($"Native Notifications: {capabilities.HasNativeNotifications}");
                Console.WriteLine($"File System Watcher: {capabilities.HasFileSystemWatcher}");
                Console.WriteLine($"System Tray: {capabilities.HasSystemTray}");
                Console.WriteLine($"Elevation Detection: {capabilities.HasElevationDetection}");
                Console.WriteLine($"Supported Features: {string.Join(", ", capabilities.SupportedFeatures)}");
                Console.WriteLine();
                
                // Test feature support methods
                Console.WriteLine("5. Testing Feature Support Methods...");
                Console.WriteLine($"Supports Native Notifications: {platformService.SupportsNativeNotifications()}");
                Console.WriteLine($"Supports File System Features: {platformService.SupportsFileSystemFeatures()}");
                Console.WriteLine();
                
                // Test notification
                Console.WriteLine("6. Testing Notification System...");
                platformService.ShowNotification("Platform Test", "Cross-platform compatibility test completed successfully!");
                Console.WriteLine("✓ Notification sent (check console output above)");
                Console.WriteLine();
                
                // Test elevation detection
                Console.WriteLine("7. Testing Elevation Detection...");
                var isElevated = platformService.IsElevated();
                Console.WriteLine($"Running with elevated privileges: {isElevated}");
                Console.WriteLine();
                
                Console.WriteLine("=== All Tests Completed Successfully! ===");
                Console.WriteLine();
                Console.WriteLine("Press any key to exit...");
                Console.ReadKey();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Test Failed: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
                Console.WriteLine();
                Console.WriteLine("Press any key to exit...");
                Console.ReadKey();
            }
        }
    }
}