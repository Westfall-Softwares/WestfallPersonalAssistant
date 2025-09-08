using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.ViewModels
{
    public class DashboardViewModel
    {
        private readonly IBusinessTaskService _taskService;
        
        public ObservableCollection<BusinessTask> Tasks { get; } = new();
        public BusinessTaskAnalytics Analytics { get; private set; } = new();
        
        public DashboardViewModel(IBusinessTaskService taskService)
        {
            _taskService = taskService;
            _ = LoadDataAsync();
        }
        
        public DashboardViewModel() : this(new BusinessTaskService())
        {
            // Default constructor for XAML designer
        }
        
        private async Task LoadDataAsync()
        {
            try
            {
                // Load tasks
                var tasks = await _taskService.GetAllTasksAsync();
                Tasks.Clear();
                
                foreach (var task in tasks)
                {
                    Tasks.Add(task);
                }
                
                // Load analytics
                Analytics = await _taskService.GetTaskAnalyticsAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading dashboard data: {ex.Message}");
            }
        }
        
        public async Task RefreshDataAsync()
        {
            await LoadDataAsync();
        }
        
        public async Task CompleteTaskAsync(string taskId)
        {
            await _taskService.CompleteTaskAsync(taskId);
            await RefreshDataAsync();
        }
    }
}