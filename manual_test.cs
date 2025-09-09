using System;
using WestfallPersonalAssistant.Services;

try 
{
    Console.WriteLine("Testing platform detection...");
    var service = PlatformService.Instance;
    Console.WriteLine($"Platform: {service.GetPlatformName()}");
    Console.WriteLine($"Supported: {PlatformService.IsCurrentPlatformSupported}");
    var caps = service.GetCapabilities();
    Console.WriteLine($"Features: {string.Join(", ", caps.SupportedFeatures)}");
    service.ShowNotification("Test", "Platform detection working!");
    Console.WriteLine("Test completed successfully!");
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
}
