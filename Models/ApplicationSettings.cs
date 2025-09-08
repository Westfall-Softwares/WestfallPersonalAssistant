using System.Text.Json.Serialization;

namespace WestfallPersonalAssistant.Models
{
    public class ApplicationSettings
    {
        [JsonPropertyName("version")]
        public string Version { get; set; } = "1.0.0";
        
        [JsonPropertyName("firstRun")]
        public bool FirstRun { get; set; } = true;
        
        [JsonPropertyName("theme")]
        public string Theme { get; set; } = "Light";
        
        [JsonPropertyName("language")]
        public string Language { get; set; } = "en-US";
        
        [JsonPropertyName("autoStartup")]
        public bool AutoStartup { get; set; } = false;
        
        [JsonPropertyName("minimizeToTray")]
        public bool MinimizeToTray { get; set; } = true;
        
        [JsonPropertyName("enableNotifications")]
        public bool EnableNotifications { get; set; } = true;
        
        [JsonPropertyName("checkForUpdates")]
        public bool CheckForUpdates { get; set; } = true;
        
        [JsonPropertyName("dataBackupEnabled")]
        public bool DataBackupEnabled { get; set; } = true;
        
        [JsonPropertyName("dataBackupFrequency")]
        public string DataBackupFrequency { get; set; } = "Weekly";
        
        [JsonPropertyName("enableAnalytics")]
        public bool EnableAnalytics { get; set; } = false;
        
        [JsonPropertyName("windowSettings")]
        public WindowSettings WindowSettings { get; set; } = new();
        
        [JsonPropertyName("tailorPackSettings")]
        public TailorPackSettings TailorPackSettings { get; set; } = new();
        
        [JsonPropertyName("businessSettings")]
        public BusinessSettings BusinessSettings { get; set; } = new();
    }
    
    public class WindowSettings
    {
        [JsonPropertyName("width")]
        public int Width { get; set; } = 1200;
        
        [JsonPropertyName("height")]
        public int Height { get; set; } = 800;
        
        [JsonPropertyName("x")]
        public int X { get; set; } = -1;
        
        [JsonPropertyName("y")]
        public int Y { get; set; } = -1;
        
        [JsonPropertyName("isMaximized")]
        public bool IsMaximized { get; set; } = false;
    }
    
    public class TailorPackSettings
    {
        [JsonPropertyName("autoLoadPacks")]
        public bool AutoLoadPacks { get; set; } = true;
        
        [JsonPropertyName("checkForPackUpdates")]
        public bool CheckForPackUpdates { get; set; } = true;
        
        [JsonPropertyName("allowBetaPacks")]
        public bool AllowBetaPacks { get; set; } = false;
        
        [JsonPropertyName("enabledPacks")]
        public string[] EnabledPacks { get; set; } = Array.Empty<string>();
        
        [JsonPropertyName("disabledPacks")]
        public string[] DisabledPacks { get; set; } = Array.Empty<string>();
    }
    
    public class BusinessSettings
    {
        [JsonPropertyName("businessName")]
        public string BusinessName { get; set; } = string.Empty;
        
        [JsonPropertyName("businessType")]
        public string BusinessType { get; set; } = "Startup";
        
        [JsonPropertyName("industry")]
        public string Industry { get; set; } = string.Empty;
        
        [JsonPropertyName("currency")]
        public string Currency { get; set; } = "USD";
        
        [JsonPropertyName("timezone")]
        public string Timezone { get; set; } = "UTC";
        
        [JsonPropertyName("fiscalYearStart")]
        public string FiscalYearStart { get; set; } = "January";
        
        [JsonPropertyName("enableGoalTracking")]
        public bool EnableGoalTracking { get; set; } = true;
        
        [JsonPropertyName("enableAnalyticsDashboard")]
        public bool EnableAnalyticsDashboard { get; set; } = true;
    }
}