using Avalonia.Controls;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;
using WestfallPersonalAssistant.Packs.Demo;
using System;

namespace WestfallPersonalAssistant
{
    public partial class MainWindow : Window
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly ISettingsManager _settingsManager;
        private readonly IDatabaseService _databaseService;
        private readonly IBusinessTaskService _businessTaskService;
        
        public MainWindow()
        {
            InitializeComponent();
            
            // Initialize services
            var platformService = PlatformService.Instance;
            _fileSystemService = new FileSystemService(platformService);
            _settingsManager = new SettingsManager(_fileSystemService);
            _databaseService = new DatabaseService(_fileSystemService);
            _businessTaskService = new DatabaseBusinessTaskService(_databaseService);
            
            InitializeServices();
        }
        
        private async void InitializeServices()
        {
            try
            {
                // Initialize platform services
                var platformService = PlatformService.Instance;
                platformService.ShowNotification(
                    "Westfall Assistant", 
                    $"Starting on {platformService.GetPlatformName()}"
                );
                
                // Initialize database
                await _databaseService.InitializeAsync();
                
                // Load settings
                var settings = await _settingsManager.LoadSettingsAsync();
                
                // Apply window settings
                if (settings.WindowSettings.Width > 0 && settings.WindowSettings.Height > 0)
                {
                    Width = settings.WindowSettings.Width;
                    Height = settings.WindowSettings.Height;
                }
                
                if (settings.WindowSettings.X >= 0 && settings.WindowSettings.Y >= 0)
                {
                    Position = new Avalonia.PixelPoint(settings.WindowSettings.X, settings.WindowSettings.Y);
                }
                
                if (settings.WindowSettings.IsMaximized)
                {
                    WindowState = WindowState.Maximized;
                }
                
                // Initialize TailorPack system
                var packManager = TailorPackManager.Instance;
                packManager.Initialize(_fileSystemService);
                
                // Load demo pack
                packManager.LoadPack("marketing-essentials");
                
                // Activate demo pack features
                packManager.ActivationService.ActivatePackFeatures("marketing-essentials");
                
                // Initialize sample data if this is the first run
                if (settings.FirstRun)
                {
                    await InitializeSampleDataAsync();
                    settings.FirstRun = false;
                    await _settingsManager.SaveSettingsAsync(settings);
                }
                
                Title = $"Westfall Assistant - Entrepreneur Edition ({platformService.GetPlatformName()})";
                
                platformService.ShowNotification(
                    "Westfall Assistant", 
                    "Ready for business!"
                );
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing services: {ex.Message}");
                Title = "Westfall Assistant - Initialization Error";
            }
        }
        
        private async System.Threading.Tasks.Task InitializeSampleDataAsync()
        {
            try
            {
                // Create sample business tasks
                var sampleTasks = new[]
                {
                    new Models.BusinessTask
                    {
                        Title = "Develop Q4 Marketing Strategy",
                        Description = "Create comprehensive marketing plan for Q4 including budget allocation and campaign timeline",
                        DueDate = DateTime.Now.AddDays(14),
                        Category = "Marketing",
                        TaskType = Models.BusinessTaskType.Strategic,
                        StrategicImportance = Models.StrategicImportance.High,
                        Priority = 1,
                        Status = "In Progress",
                        EstimatedHours = 20,
                        RevenueImpact = 50000,
                        Tags = "strategy,marketing,q4"
                    },
                    new Models.BusinessTask
                    {
                        Title = "Customer Feedback Survey",
                        Description = "Design and launch customer satisfaction survey to improve service quality",
                        DueDate = DateTime.Now.AddDays(7),
                        Category = "Customer Service",
                        TaskType = Models.BusinessTaskType.CustomerService,
                        StrategicImportance = Models.StrategicImportance.Medium,
                        Priority = 2,
                        Status = "Pending",
                        EstimatedHours = 8,
                        Tags = "survey,customers,feedback"
                    },
                    new Models.BusinessTask
                    {
                        Title = "Update Financial Projections",
                        Description = "Revise Q4 and 2024 financial forecasts based on current performance",
                        DueDate = DateTime.Now.AddDays(5),
                        Category = "Finance",
                        TaskType = Models.BusinessTaskType.Finance,
                        StrategicImportance = Models.StrategicImportance.Critical,
                        Priority = 1,
                        Status = "Pending",
                        EstimatedHours = 12,
                        Tags = "finance,projections,forecasting"
                    }
                };
                
                foreach (var task in sampleTasks)
                {
                    await _businessTaskService.CreateTaskAsync(task);
                }
                
                Console.WriteLine("Sample data initialized successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing sample data: {ex.Message}");
            }
        }
        
        protected override async void OnClosing(WindowClosingEventArgs e)
        {
            try
            {
                // Save current window settings
                var settings = _settingsManager.GetCurrentSettings();
                settings.WindowSettings.Width = (int)Width;
                settings.WindowSettings.Height = (int)Height;
                settings.WindowSettings.X = (int)Position.X;
                settings.WindowSettings.Y = (int)Position.Y;
                settings.WindowSettings.IsMaximized = WindowState == WindowState.Maximized;
                
                await _settingsManager.SaveSettingsAsync(settings);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving settings on close: {ex.Message}");
            }
            
            base.OnClosing(e);
        }
    }
}