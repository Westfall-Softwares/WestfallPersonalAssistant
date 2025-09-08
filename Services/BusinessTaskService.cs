using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public class BusinessTaskService : IBusinessTaskService
    {
        private readonly List<BusinessTask> _tasks = new();
        
        public event EventHandler<BusinessTask>? TaskCreated;
        public event EventHandler<BusinessTask>? TaskUpdated;
        public event EventHandler<BusinessTask>? TaskCompleted;
        public event EventHandler<string>? TaskDeleted;
        
        public BusinessTaskService()
        {
            InitializeSampleTasks();
        }
        
        private void InitializeSampleTasks()
        {
            _tasks.AddRange(new[]
            {
                new BusinessTask
                {
                    Title = "Develop Q4 Marketing Strategy",
                    Description = "Create comprehensive marketing plan for Q4 including budget allocation and campaign timeline",
                    DueDate = DateTime.Now.AddDays(14),
                    Category = "Marketing",
                    TaskType = BusinessTaskType.Strategic,
                    StrategicImportance = StrategicImportance.High,
                    Priority = 1,
                    Status = "In Progress",
                    EstimatedHours = 20,
                    RevenueImpact = 50000,
                    Tags = "strategy,marketing,q4"
                },
                new BusinessTask
                {
                    Title = "Customer Feedback Survey",
                    Description = "Design and launch customer satisfaction survey to improve service quality",
                    DueDate = DateTime.Now.AddDays(7),
                    Category = "Customer Service",
                    TaskType = BusinessTaskType.CustomerService,
                    StrategicImportance = StrategicImportance.Medium,
                    Priority = 2,
                    Status = "Pending",
                    EstimatedHours = 8,
                    Tags = "survey,customers,feedback"
                },
                new BusinessTask
                {
                    Title = "Competitor Analysis Report",
                    Description = "Analyze top 5 competitors' pricing, features, and market positioning",
                    DueDate = DateTime.Now.AddDays(10),
                    Category = "Research",
                    TaskType = BusinessTaskType.Research,
                    StrategicImportance = StrategicImportance.High,
                    Priority = 1,
                    Status = "Pending",
                    EstimatedHours = 15,
                    Tags = "research,competitors,analysis"
                },
                new BusinessTask
                {
                    Title = "Update Financial Projections",
                    Description = "Revise Q4 and 2024 financial forecasts based on current performance",
                    DueDate = DateTime.Now.AddDays(5),
                    Category = "Finance",
                    TaskType = BusinessTaskType.Finance,
                    StrategicImportance = StrategicImportance.Critical,
                    Priority = 1,
                    Status = "Pending",
                    EstimatedHours = 12,
                    RevenueImpact = 0,
                    Tags = "finance,projections,forecasting"
                },
                new BusinessTask
                {
                    Title = "Social Media Content Calendar",
                    Description = "Create content calendar for next month's social media posts",
                    DueDate = DateTime.Now.AddDays(3),
                    Category = "Marketing",
                    TaskType = BusinessTaskType.Marketing,
                    StrategicImportance = StrategicImportance.Medium,
                    Priority = 2,
                    Status = "Pending",
                    EstimatedHours = 6,
                    Tags = "social-media,content,calendar"
                }
            });
        }
        
        public Task<BusinessTask[]> GetAllTasksAsync()
        {
            return Task.FromResult(_tasks.ToArray());
        }
        
        public Task<BusinessTask[]> GetTasksByTypeAsync(BusinessTaskType taskType)
        {
            var filteredTasks = _tasks.Where(t => t.TaskType == taskType).ToArray();
            return Task.FromResult(filteredTasks);
        }
        
        public Task<BusinessTask[]> GetTasksByStatusAsync(string status)
        {
            var filteredTasks = _tasks.Where(t => t.Status.Equals(status, StringComparison.OrdinalIgnoreCase)).ToArray();
            return Task.FromResult(filteredTasks);
        }
        
        public Task<BusinessTask[]> GetOverdueTasksAsync()
        {
            var overdueTasks = _tasks.Where(t => !t.IsCompleted && t.DueDate < DateTime.Now).ToArray();
            return Task.FromResult(overdueTasks);
        }
        
        public Task<BusinessTask[]> GetTasksDueTodayAsync()
        {
            var today = DateTime.Today;
            var tasksDueToday = _tasks.Where(t => !t.IsCompleted && t.DueDate.Date == today).ToArray();
            return Task.FromResult(tasksDueToday);
        }
        
        public Task<BusinessTask> CreateTaskAsync(BusinessTask task)
        {
            task.Id = Guid.NewGuid().ToString();
            task.CreatedDate = DateTime.Now;
            _tasks.Add(task);
            
            TaskCreated?.Invoke(this, task);
            return Task.FromResult(task);
        }
        
        public Task<BusinessTask> UpdateTaskAsync(BusinessTask task)
        {
            var existingTask = _tasks.FirstOrDefault(t => t.Id == task.Id);
            if (existingTask != null)
            {
                var index = _tasks.IndexOf(existingTask);
                _tasks[index] = task;
                TaskUpdated?.Invoke(this, task);
            }
            
            return Task.FromResult(task);
        }
        
        public Task<bool> DeleteTaskAsync(string taskId)
        {
            var task = _tasks.FirstOrDefault(t => t.Id == taskId);
            if (task != null)
            {
                _tasks.Remove(task);
                TaskDeleted?.Invoke(this, taskId);
                return Task.FromResult(true);
            }
            
            return Task.FromResult(false);
        }
        
        public Task<bool> CompleteTaskAsync(string taskId)
        {
            var task = _tasks.FirstOrDefault(t => t.Id == taskId);
            if (task != null)
            {
                task.IsCompleted = true;
                task.CompletedDate = DateTime.Now;
                task.Status = "Completed";
                TaskCompleted?.Invoke(this, task);
                return Task.FromResult(true);
            }
            
            return Task.FromResult(false);
        }
        
        public Task<BusinessTaskAnalytics> GetTaskAnalyticsAsync()
        {
            var analytics = new BusinessTaskAnalytics
            {
                TotalTasks = _tasks.Count,
                CompletedTasks = _tasks.Count(t => t.IsCompleted),
                OverdueTasks = _tasks.Count(t => !t.IsCompleted && t.DueDate < DateTime.Now),
                TasksDueToday = _tasks.Count(t => !t.IsCompleted && t.DueDate.Date == DateTime.Today)
            };
            
            analytics.CompletionRate = analytics.TotalTasks > 0 
                ? (double)analytics.CompletedTasks / analytics.TotalTasks * 100 
                : 0;
            
            // Group tasks by type
            foreach (BusinessTaskType taskType in Enum.GetValues<BusinessTaskType>())
            {
                analytics.TasksByType[taskType] = _tasks.Count(t => t.TaskType == taskType);
            }
            
            // Group tasks by importance
            foreach (StrategicImportance importance in Enum.GetValues<StrategicImportance>())
            {
                analytics.TasksByImportance[importance] = _tasks.Count(t => t.StrategicImportance == importance);
            }
            
            analytics.TotalRevenueImpact = _tasks.Where(t => t.RevenueImpact.HasValue).Sum(t => t.RevenueImpact!.Value);
            analytics.AverageHoursPerTask = _tasks.Count > 0 ? _tasks.Average(t => t.EstimatedHours) : 0;
            
            return Task.FromResult(analytics);
        }
    }
}