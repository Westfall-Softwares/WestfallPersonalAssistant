using Avalonia.Controls;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;
using WestfallPersonalAssistant.Packs.Demo;

namespace WestfallPersonalAssistant
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            InitializeServices();
        }
        
        private void InitializeServices()
        {
            // Initialize platform services
            var platformService = PlatformService.Instance;
            platformService.ShowNotification(
                "Westfall Assistant", 
                $"Running on {platformService.GetPlatformName()}"
            );
            
            // Initialize TailorPack system
            var packManager = TailorPackManager.Instance;
            
            // Load demo pack
            var demoPack = new MarketingEssentialsPack();
            demoPack.Initialize();
            
            Title = $"Westfall Assistant - Entrepreneur Edition ({platformService.GetPlatformName()})";
        }
    }
}