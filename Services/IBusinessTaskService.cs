using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public interface IBusinessTaskService
    {
        Task<BusinessTask[]> GetAllTasksAsync();
        Task<BusinessTask[]> GetTasksByTypeAsync(BusinessTaskType taskType);
        Task<BusinessTask[]> GetTasksByStatusAsync(string status);
        Task<BusinessTask[]> GetOverdueTasksAsync();
        Task<BusinessTask[]> GetTasksDueTodayAsync();
        Task<BusinessTask> CreateTaskAsync(BusinessTask task);
        Task<BusinessTask> UpdateTaskAsync(BusinessTask task);
        Task<bool> DeleteTaskAsync(string taskId);
        Task<bool> CompleteTaskAsync(string taskId);
        Task<BusinessTaskAnalytics> GetTaskAnalyticsAsync();
        
        event EventHandler<BusinessTask>? TaskCreated;
        event EventHandler<BusinessTask>? TaskUpdated;
        event EventHandler<BusinessTask>? TaskCompleted;
        event EventHandler<string>? TaskDeleted;
    }
    
    public class BusinessTaskAnalytics
    {
        public int TotalTasks { get; set; }
        public int CompletedTasks { get; set; }
        public int OverdueTasks { get; set; }
        public int TasksDueToday { get; set; }
        public double CompletionRate { get; set; }
        public Dictionary<BusinessTaskType, int> TasksByType { get; set; } = new();
        public Dictionary<StrategicImportance, int> TasksByImportance { get; set; } = new();
        public decimal TotalRevenueImpact { get; set; }
        public double AverageHoursPerTask { get; set; }
    }
}