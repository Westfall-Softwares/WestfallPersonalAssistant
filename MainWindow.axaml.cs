using Avalonia.Controls;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;
using WestfallPersonalAssistant.Packs.Demo;

namespace WestfallPersonalAssistant
{
    public partial class MainWindow : Window
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly ISettingsManager _settingsManager;
        
        public MainWindow()
        {
            InitializeComponent();
            
            // Initialize services
            var platformService = PlatformService.Instance;
            _fileSystemService = new FileSystemService(platformService);
            _settingsManager = new SettingsManager(_fileSystemService);
            
            InitializeServices();
        }
        
        private async void InitializeServices()
        {
            // Initialize platform services
            var platformService = PlatformService.Instance;
            platformService.ShowNotification(
                "Westfall Assistant", 
                $"Running on {platformService.GetPlatformName()}"
            );
            
            // Load settings
            await _settingsManager.LoadSettingsAsync();
            
            // Initialize TailorPack system
            var packManager = TailorPackManager.Instance;
            packManager.Initialize(_fileSystemService);
            
            // Load demo pack
            var demoPack = new MarketingEssentialsPack();
            packManager.LoadPack("marketing-essentials");
            
            // Activate demo pack features
            packManager.ActivationService.ActivatePackFeatures("marketing-essentials");
            
            Title = $"Westfall Assistant - Entrepreneur Edition ({platformService.GetPlatformName()})";
        }
        
        protected override async void OnClosing(WindowClosingEventArgs e)
        {
            // Save current window settings
            var settings = _settingsManager.GetCurrentSettings();
            settings.WindowSettings.Width = (int)Width;
            settings.WindowSettings.Height = (int)Height;
            settings.WindowSettings.X = (int)Position.X;
            settings.WindowSettings.Y = (int)Position.Y;
            settings.WindowSettings.IsMaximized = WindowState == WindowState.Maximized;
            
            await _settingsManager.SaveSettingsAsync(settings);
            
            base.OnClosing(e);
        }
    }
}