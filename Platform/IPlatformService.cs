namespace WestfallPersonalAssistant.Platform
{
    public interface IPlatformService
    {
        string GetPlatformName();
        string GetAppDataPath();
        void ShowNotification(string title, string message);
        bool IsElevated();
    }
}