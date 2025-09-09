using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using Avalonia.Threading;
using WestfallPersonalAssistant.Models;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.ViewModels
{
    public class DashboardViewModel : INotifyPropertyChanged
    {
        private readonly IBusinessTaskService _taskService;
        private bool _isLoading;
        private string _statusMessage = string.Empty;
        
        public ObservableCollection<BusinessTask> Tasks { get; } = new();
        public BusinessTaskAnalytics Analytics { get; private set; } = new();

        public bool IsLoading
        {
            get => _isLoading;
            private set
            {
                _isLoading = value;
                OnPropertyChanged();
            }
        }

        public string StatusMessage
        {
            get => _statusMessage;
            private set
            {
                _statusMessage = value;
                OnPropertyChanged();
            }
        }
        
        public DashboardViewModel(IBusinessTaskService taskService)
        {
            _taskService = taskService;
            // Don't block the constructor - initialize asynchronously
            _ = InitializeAsync();
        }
        
        public DashboardViewModel() : this(new BusinessTaskService())
        {
            // Default constructor for XAML designer
        }

        /// <summary>
        /// Initialize dashboard asynchronously without blocking the UI
        /// </summary>
        private async Task InitializeAsync()
        {
            try
            {
                IsLoading = true;
                StatusMessage = "Initializing dashboard...";
                
                // Load data asynchronously on background thread
                await Task.Run(async () =>
                {
                    await LoadDataAsync();
                });
                
                StatusMessage = "Dashboard ready";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing dashboard: {ex.Message}");
                StatusMessage = "Failed to load dashboard data";
            }
            finally
            {
                IsLoading = false;
            }
        }
        
        private async Task LoadDataAsync()
        {
            try
            {
                StatusMessage = "Loading tasks...";
                
                // Load tasks
                var tasks = await _taskService.GetAllTasksAsync();
                
                // Update UI on main thread
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    Tasks.Clear();
                    foreach (var task in tasks)
                    {
                        Tasks.Add(task);
                    }
                });
                
                StatusMessage = "Loading analytics...";
                
                // Load analytics
                var analytics = await _taskService.GetTaskAnalyticsAsync();
                
                // Update UI on main thread
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    Analytics = analytics;
                    OnPropertyChanged(nameof(Analytics));
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading dashboard data: {ex.Message}");
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    StatusMessage = $"Error loading data: {ex.Message}";
                });
            }
        }
        
        public async Task RefreshDataAsync()
        {
            if (IsLoading) return; // Prevent multiple simultaneous refreshes
            
            try
            {
                IsLoading = true;
                StatusMessage = "Refreshing data...";
                
                await Task.Run(async () =>
                {
                    await LoadDataAsync();
                });
                
                StatusMessage = "Data refreshed successfully";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error refreshing data: {ex.Message}");
                StatusMessage = $"Refresh failed: {ex.Message}";
            }
            finally
            {
                IsLoading = false;
                
                // Clear status message after a delay
                _ = Task.Delay(2000).ContinueWith(_ =>
                {
                    if (!IsLoading)
                    {
                        Dispatcher.UIThread.InvokeAsync(() =>
                        {
                            StatusMessage = string.Empty;
                        });
                    }
                });
            }
        }
        
        public async Task CompleteTaskAsync(string taskId)
        {
            try
            {
                StatusMessage = "Completing task...";
                
                await Task.Run(async () =>
                {
                    await _taskService.CompleteTaskAsync(taskId);
                });
                
                await RefreshDataAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error completing task: {ex.Message}");
                StatusMessage = $"Failed to complete task: {ex.Message}";
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        
        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}