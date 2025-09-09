using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Packs.Demo
{
    public class MarketingEssentialsPack : ITailorPack
    {
        private readonly TailorPackManifest _manifest;
        private readonly IFeature[] _features;
        
        public MarketingEssentialsPack()
        {
            _manifest = new TailorPackManifest
            {
                Id = "marketing-essentials",
                Name = "Marketing Essentials Pack",
                Description = "Campaign tracking, social media management, lead generation tools",
                Version = "1.0.0",
                Author = "Westfall Business Tools",
                SupportedPlatforms = new[] { "Windows", "macOS", "Linux" },
                Dependencies = Array.Empty<string>()
            };
            
            _features = new IFeature[]
            {
                new CampaignTrackingFeature(),
                new SocialMediaFeature(),
                new LeadGenerationFeature(),
                new EmailMarketingFeature(),
                new AnalyticsFeature()
            };
        }
        
        public void Initialize()
        {
            Console.WriteLine("Initializing Marketing Essentials Pack...");
            foreach (var feature in _features)
            {
                feature.Initialize();
            }
        }
        
        public void Shutdown()
        {
            Console.WriteLine("Shutting down Marketing Essentials Pack...");
            foreach (var feature in _features)
            {
                feature.Shutdown();
            }
        }
        
        public TailorPackManifest GetManifest() => _manifest;
        
        public IFeature[] GetFeatures() => _features;
    }
    
    // Demo features
    public class CampaignTrackingFeature : IFeature
    {
        public string Id => "campaign-tracking";
        public string Name => "Campaign Tracking";
        public string Description => "Track marketing campaign performance and ROI";
        
        public void Initialize() => Console.WriteLine("Campaign Tracking feature initialized");
        public void Shutdown() => Console.WriteLine("Campaign Tracking feature shutdown");
    }
    
    public class SocialMediaFeature : IFeature
    {
        public string Id => "social-media";
        public string Name => "Social Media Management";
        public string Description => "Manage social media posts and engagement";
        
        public void Initialize() => Console.WriteLine("Social Media Management feature initialized");
        public void Shutdown() => Console.WriteLine("Social Media Management feature shutdown");
    }
    
    public class LeadGenerationFeature : IFeature
    {
        public string Id => "lead-generation";
        public string Name => "Lead Generation";
        public string Description => "Generate and manage business leads";
        
        public void Initialize() => Console.WriteLine("Lead Generation feature initialized");
        public void Shutdown() => Console.WriteLine("Lead Generation feature shutdown");
    }
    
    public class EmailMarketingFeature : IFeature
    {
        public string Id => "email-marketing";
        public string Name => "Email Marketing";
        public string Description => "Create and send marketing email campaigns";
        
        public void Initialize() => Console.WriteLine("Email Marketing feature initialized");
        public void Shutdown() => Console.WriteLine("Email Marketing feature shutdown");
    }
    
    public class AnalyticsFeature : IFeature
    {
        public string Id => "analytics";
        public string Name => "Marketing Analytics";
        public string Description => "Analyze marketing performance and metrics";
        
        public void Initialize() => Console.WriteLine("Marketing Analytics feature initialized");
        public void Shutdown() => Console.WriteLine("Marketing Analytics feature shutdown");
    }
}