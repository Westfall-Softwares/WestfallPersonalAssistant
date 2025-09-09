using System;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Demo;

class DemoProgram
{
    static async Task Main(string[] args)
    {
        try
        {
            await TodoFixesDemo.RunDemoAsync();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Demo error: {ex.Message}");
        }
        
        Console.WriteLine("\nPress any key to exit...");
        Console.ReadKey();
    }
}