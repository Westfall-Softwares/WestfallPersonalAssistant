using Avalonia.Controls;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.TailorPack;
using WestfallPersonalAssistant.Packs.Demo;
using WestfallPersonalAssistant.Views;
using WestfallPersonalAssistant.ViewModels;
using System;
using System.Windows.Input;

namespace WestfallPersonalAssistant
{
    public partial class MainWindow : Window
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly ISettingsManager _settingsManager;
        private readonly IDatabaseService _databaseService;
        private readonly IBusinessTaskService _businessTaskService;
        private readonly IBusinessGoalService _businessGoalService;
        private readonly IAccessibilityService _accessibilityService;
        private AccessibilitySettingsView _accessibilitySettingsView;
        
        public ICommand SwitchToDashboardCommand { get; private set; }
        public ICommand SwitchToAnalyticsCommand { get; private set; }
        public ICommand SwitchToPacksCommand { get; private set; }
        public ICommand ShowAccessibilityHelpCommand { get; private set; }
        public ICommand OpenAccessibilitySettingsCommand { get; private set; }
        
        public MainWindow()
        {
            InitializeComponent();
            
            // Initialize services
            var platformService = PlatformService.Instance;
            _fileSystemService = new FileSystemService(platformService);
            _settingsManager = new SettingsManager(_fileSystemService);
            _databaseService = new DatabaseService(_fileSystemService);
            _businessTaskService = new DatabaseBusinessTaskService(_databaseService);
            _businessGoalService = new DatabaseBusinessGoalService(_databaseService);
            _accessibilityService = new AccessibilityService(_settingsManager);
            
            // Initialize commands
            InitializeCommands();
            
            // Set DataContext for command binding
            DataContext = this;
            
            InitializeServices();
        }
        
        private void InitializeCommands()
        {
            SwitchToDashboardCommand = new RelayCommand(() => {
                if (MainTabControl != null) 
                {
                    MainTabControl.SelectedIndex = 0;
                    _accessibilityService.AnnounceToScreenReader("Switched to Dashboard");
                }
            });
            
            SwitchToAnalyticsCommand = new RelayCommand(() => {
                if (MainTabControl != null) 
                {
                    MainTabControl.SelectedIndex = 1;
                    _accessibilityService.AnnounceToScreenReader("Switched to Analytics");
                }
            });
            
            SwitchToPacksCommand = new RelayCommand(() => {
                if (MainTabControl != null) 
                {
                    MainTabControl.SelectedIndex = 2;
                    _accessibilityService.AnnounceToScreenReader("Switched to Tailor Packs");
                }
            });
            
            ShowAccessibilityHelpCommand = new RelayCommand(() => {
                var helpMessage = @"Accessibility Help:
                
Keyboard Shortcuts:
- Ctrl+1: Switch to Dashboard
- Ctrl+2: Switch to Analytics  
- Ctrl+3: Switch to Tailor Packs
- Ctrl+Alt+A: Open Accessibility Settings
- F1: Show this help
- Tab: Navigate forward
- Shift+Tab: Navigate backward
- Enter: Activate focused element
- Escape: Close dialogs

Features:
- Screen reader support with ARIA labels
- High contrast mode available
- Text size adjustment (80% to 200%)
- Focus indicators
- Keyboard-only navigation

Press Ctrl+Alt+A to open accessibility settings.";
                
                _accessibilityService.AnnounceToScreenReader(helpMessage);
            });
            
            OpenAccessibilitySettingsCommand = new RelayCommand(() => {
                ShowAccessibilitySettings();
            });
        }
        
        private void ShowAccessibilitySettings()
        {
            if (_accessibilitySettingsView == null)
            {
                _accessibilitySettingsView = new AccessibilitySettingsView();
                var viewModel = new AccessibilitySettingsViewModel(_accessibilityService);
                
                viewModel.CloseRequested += (s, e) => {
                    _accessibilitySettingsView.IsVisible = false;
                    _accessibilityService.AnnounceToScreenReader("Accessibility settings closed");
                };
                
                _accessibilitySettingsView.DataContext = viewModel;
            }
            
            // Show accessibility settings in a new window or overlay
            var settingsWindow = new Window
            {
                Title = "Accessibility Settings",
                Content = _accessibilitySettingsView,
                Width = 600,
                Height = 800,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                CanResize = true
            };
            
            settingsWindow.Show(this);
            _accessibilityService.AnnounceToScreenReader("Accessibility settings opened");
        }
        
        private async void InitializeServices()
        {
            try
            {
                // Phase 1: Quick startup - Initialize only essential services for UI
                Title = "Westfall Assistant - Starting...";
                
                // Show immediate feedback
                var platformService = PlatformService.Instance;
                platformService.ShowNotification(
                    "Westfall Assistant", 
                    $"Starting on {platformService.GetPlatformName()}"
                );
                
                // Phase 2: Background initialization of non-critical services
                await Task.Run(async () =>
                {
                    // Initialize database in background
                    await _databaseService.InitializeAsync();
                    
                    // Load settings asynchronously
                    var settings = await _settingsManager.LoadSettingsAsync();
                    
                    // Apply window settings on UI thread
                    await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        ApplyWindowSettings(settings);
                    });
                    
                    // Phase 3: Initialize TailorPack system with progress
                    var progress = new Progress<ProgressInfo>(info =>
                    {
                        Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                        {
                            Title = $"Westfall Assistant - {info.Message}";
                        });
                    });
                    
                    var packManager = TailorPackManager.Instance;
                    packManager.Initialize(_fileSystemService);
                    
                    // Load demo pack asynchronously with progress
                    await packManager.LoadPackAsync("marketing-essentials", progress);
                    
                    // Activate demo pack features
                    packManager.ActivationService.ActivatePackFeatures("marketing-essentials");
                    
                    // Phase 4: Initialize sample data only if needed (first run)
                    if (settings.FirstRun)
                    {
                        await InitializeSampleDataAsync();
                        settings.FirstRun = false;
                        await _settingsManager.SaveSettingsAsync(settings);
                    }
                    
                    // Final UI update
                    await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        Title = $"Westfall Assistant - Entrepreneur Edition ({platformService.GetPlatformName()})";
                        
                        platformService.ShowNotification(
                            "Westfall Assistant", 
                            "Ready for business!"
                        );
                    });
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing services: {ex.Message}");
                Title = "Westfall Assistant - Initialization Error";
            }
        }
        
        private void ApplyWindowSettings(Models.ApplicationSettings settings)
        {
            // Apply window settings on UI thread
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
        }
        
        private async System.Threading.Tasks.Task InitializeSampleDataAsync()
        {
            try
            {
                // Use parallel processing for better performance
                var taskCreationTasks = new List<Task>();
                var goalCreationTasks = new List<Task>();
                
                // Create sample business tasks in parallel
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
                
                // Create sample business goals
                var sampleGoals = new[]
                {
                    new Models.BusinessGoal
                    {
                        Title = "Reach $100K Annual Revenue",
                        Description = "Achieve $100,000 in annual recurring revenue through product sales and services",
                        TargetValue = 100000,
                        CurrentValue = 45000,
                        Unit = "USD",
                        Category = "Revenue",
                        GoalType = Models.BusinessGoalType.Revenue,
                        Priority = Models.GoalPriority.Critical,
                        StartDate = DateTime.Now.AddMonths(-6),
                        TargetDate = DateTime.Now.AddMonths(6)
                    },
                    new Models.BusinessGoal
                    {
                        Title = "Acquire 500 New Customers",
                        Description = "Grow customer base to 500 active paying customers",
                        TargetValue = 500,
                        CurrentValue = 247,
                        Unit = "customers",
                        Category = "Growth",
                        GoalType = Models.BusinessGoalType.Customers,
                        Priority = Models.GoalPriority.High,
                        StartDate = DateTime.Now.AddMonths(-3),
                        TargetDate = DateTime.Now.AddMonths(9)
                    },
                    new Models.BusinessGoal
                    {
                        Title = "Launch Marketing Campaign",
                        Description = "Execute comprehensive digital marketing campaign with 5% conversion rate",
                        TargetValue = 5,
                        CurrentValue = 2.8m,
                        Unit = "percent",
                        Category = "Marketing",
                        GoalType = Models.BusinessGoalType.Marketing,
                        Priority = Models.GoalPriority.Medium,
                        StartDate = DateTime.Now.AddDays(-30),
                        TargetDate = DateTime.Now.AddDays(60)
                    }
                };
                
                // Create tasks in parallel for better performance
                foreach (var task in sampleTasks)
                {
                    taskCreationTasks.Add(_businessTaskService.CreateTaskAsync(task));
                }
                
                foreach (var goal in sampleGoals)
                {
                    goalCreationTasks.Add(_businessGoalService.CreateGoalAsync(goal));
                }
                
                // Wait for all tasks and goals to be created
                await Task.WhenAll(taskCreationTasks);
                await Task.WhenAll(goalCreationTasks);
                
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