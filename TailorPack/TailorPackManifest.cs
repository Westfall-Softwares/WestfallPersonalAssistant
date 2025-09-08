using System.Text.Json.Serialization;

namespace WestfallPersonalAssistant.TailorPack
{
    public class TailorPackManifest
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;
        
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;
        
        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;
        
        [JsonPropertyName("version")]
        public string Version { get; set; } = string.Empty;
        
        [JsonPropertyName("author")]
        public string Author { get; set; } = string.Empty;
        
        [JsonPropertyName("supportedPlatforms")]
        public string[] SupportedPlatforms { get; set; } = Array.Empty<string>();
        
        [JsonPropertyName("dependencies")]
        public string[] Dependencies { get; set; } = Array.Empty<string>();
    }
}