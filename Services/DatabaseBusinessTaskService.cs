using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public class DatabaseBusinessTaskService : IBusinessTaskService
    {
        private readonly IDatabaseService _databaseService;
        
        public event EventHandler<BusinessTask>? TaskCreated;
        public event EventHandler<BusinessTask>? TaskUpdated;
        public event EventHandler<BusinessTask>? TaskCompleted;
        public event EventHandler<string>? TaskDeleted;
        
        public DatabaseBusinessTaskService(IDatabaseService databaseService)
        {
            _databaseService = databaseService;
        }
        
        public async Task<BusinessTask[]> GetAllTasksAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                       CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                       ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                       RevenueImpact, StrategicImportance
                FROM BusinessTasks 
                ORDER BY Priority, DueDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessTask);
        }
        
        public async Task<BusinessTask[]> GetTasksByTypeAsync(BusinessTaskType taskType)
        {
            const string sql = @"
                SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                       CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                       ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                       RevenueImpact, StrategicImportance
                FROM BusinessTasks 
                WHERE TaskType = @p0
                ORDER BY Priority, DueDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessTask, (int)taskType);
        }
        
        public async Task<BusinessTask[]> GetTasksByStatusAsync(string status)
        {
            const string sql = @"
                SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                       CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                       ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                       RevenueImpact, StrategicImportance
                FROM BusinessTasks 
                WHERE Status = @p0
                ORDER BY Priority, DueDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessTask, status);
        }
        
        public async Task<BusinessTask[]> GetOverdueTasksAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                       CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                       ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                       RevenueImpact, StrategicImportance
                FROM BusinessTasks 
                WHERE IsCompleted = 0 AND DueDate < @p0
                ORDER BY DueDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessTask, DateTime.Now.ToString("O"));
        }
        
        public async Task<BusinessTask[]> GetTasksDueTodayAsync()
        {
            var today = DateTime.Today;
            var tomorrow = today.AddDays(1);
            
            const string sql = @"
                SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                       CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                       ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                       RevenueImpact, StrategicImportance
                FROM BusinessTasks 
                WHERE IsCompleted = 0 AND DueDate >= @p0 AND DueDate < @p1
                ORDER BY Priority, DueDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessTask, 
                today.ToString("O"), tomorrow.ToString("O"));
        }
        
        public async Task<BusinessTask> CreateTaskAsync(BusinessTask task)
        {
            const string sql = @"
                INSERT INTO BusinessTasks (
                    Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                    CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                    ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                    RevenueImpact, StrategicImportance
                ) VALUES (
                    @p0, @p1, @p2, @p3, @p4, @p5, @p6, @p7, @p8, @p9, @p10, 
                    @p11, @p12, @p13, @p14, @p15, @p16, @p17, @p18, @p19
                )";
            
            task.Id = Guid.NewGuid().ToString();
            task.CreatedDate = DateTime.Now;
            
            await _databaseService.ExecuteNonQueryAsync(sql,
                task.Id, task.Title, task.Description, task.DueDate.ToString("O"), 
                task.Category, task.IsCompleted ? 1 : 0, task.Priority,
                task.CreatedDate.ToString("O"), task.CompletedDate?.ToString("O") ?? string.Empty,
                task.Status ?? string.Empty, task.AssignedTo ?? string.Empty, task.EstimatedHours, task.ActualHours,
                task.Tags ?? string.Empty, task.BusinessImpact ?? string.Empty, task.ProjectId ?? string.Empty, task.ClientId ?? string.Empty,
                (int)task.TaskType, task.RevenueImpact ?? 0, (int)task.StrategicImportance);
            
            TaskCreated?.Invoke(this, task);
            return task;
        }
        
        public async Task<BusinessTask> UpdateTaskAsync(BusinessTask task)
        {
            const string sql = @"
                UPDATE BusinessTasks SET 
                    Title = @p1, Description = @p2, DueDate = @p3, Category = @p4, 
                    IsCompleted = @p5, Priority = @p6, CompletedDate = @p7, Status = @p8, 
                    AssignedTo = @p9, EstimatedHours = @p10, ActualHours = @p11, Tags = @p12, 
                    BusinessImpact = @p13, ProjectId = @p14, ClientId = @p15, TaskType = @p16, 
                    RevenueImpact = @p17, StrategicImportance = @p18
                WHERE Id = @p0";
            
            await _databaseService.ExecuteNonQueryAsync(sql,
                task.Id, task.Title, task.Description, task.DueDate.ToString("O"),
                task.Category, task.IsCompleted ? 1 : 0, task.Priority,
                task.CompletedDate?.ToString("O") ?? string.Empty, task.Status ?? string.Empty, task.AssignedTo ?? string.Empty,
                task.EstimatedHours, task.ActualHours, task.Tags ?? string.Empty, task.BusinessImpact ?? string.Empty,
                task.ProjectId ?? string.Empty, task.ClientId ?? string.Empty, (int)task.TaskType, task.RevenueImpact ?? 0,
                (int)task.StrategicImportance);
            
            TaskUpdated?.Invoke(this, task);
            return task;
        }
        
        public async Task<bool> DeleteTaskAsync(string taskId)
        {
            const string sql = "DELETE FROM BusinessTasks WHERE Id = @p0";
            var rowsAffected = await _databaseService.ExecuteNonQueryAsync(sql, taskId);
            
            if (rowsAffected > 0)
            {
                TaskDeleted?.Invoke(this, taskId);
                return true;
            }
            
            return false;
        }
        
        public async Task<bool> CompleteTaskAsync(string taskId)
        {
            const string sql = @"
                UPDATE BusinessTasks 
                SET IsCompleted = 1, CompletedDate = @p1, Status = 'Completed' 
                WHERE Id = @p0";
            
            var completedDate = DateTime.Now.ToString("O");
            var rowsAffected = await _databaseService.ExecuteNonQueryAsync(sql, taskId, completedDate);
            
            if (rowsAffected > 0)
            {
                // Get the updated task to fire the event
                const string getTaskSql = @"
                    SELECT Id, Title, Description, DueDate, Category, IsCompleted, Priority, 
                           CreatedDate, CompletedDate, Status, AssignedTo, EstimatedHours, 
                           ActualHours, Tags, BusinessImpact, ProjectId, ClientId, TaskType, 
                           RevenueImpact, StrategicImportance
                    FROM BusinessTasks WHERE Id = @p0";
                
                var tasks = await _databaseService.QueryAsync(getTaskSql, MapBusinessTask, taskId);
                if (tasks.Length > 0)
                {
                    TaskCompleted?.Invoke(this, tasks[0]);
                }
                
                return true;
            }
            
            return false;
        }
        
        public async Task<BusinessTaskAnalytics> GetTaskAnalyticsAsync()
        {
            var analytics = new BusinessTaskAnalytics();
            
            // Get basic counts
            var totalTasks = await _databaseService.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM BusinessTasks");
            analytics.TotalTasks = totalTasks ?? 0;
            
            var completedTasks = await _databaseService.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM BusinessTasks WHERE IsCompleted = 1");
            analytics.CompletedTasks = completedTasks ?? 0;
            
            var overdueTasks = await _databaseService.ExecuteScalarAsync<int>(
                "SELECT COUNT(*) FROM BusinessTasks WHERE IsCompleted = 0 AND DueDate < @p0", 
                DateTime.Now.ToString("O"));
            analytics.OverdueTasks = overdueTasks ?? 0;
            
            var today = DateTime.Today;
            var tomorrow = today.AddDays(1);
            var tasksDueToday = await _databaseService.ExecuteScalarAsync<int>(
                "SELECT COUNT(*) FROM BusinessTasks WHERE IsCompleted = 0 AND DueDate >= @p0 AND DueDate < @p1",
                today.ToString("O"), tomorrow.ToString("O"));
            analytics.TasksDueToday = tasksDueToday ?? 0;
            
            // Calculate completion rate
            analytics.CompletionRate = analytics.TotalTasks > 0 
                ? (double)analytics.CompletedTasks / analytics.TotalTasks * 100 
                : 0;
            
            // Get tasks by type
            const string taskTypesSql = "SELECT TaskType, COUNT(*) FROM BusinessTasks GROUP BY TaskType";
            var taskTypeCounts = await _databaseService.QueryAsync(taskTypesSql, 
                values => new { Type = (BusinessTaskType)(int)values[0], Count = (int)values[1] });
            
            foreach (var item in taskTypeCounts)
            {
                analytics.TasksByType[item.Type] = item.Count;
            }
            
            // Get tasks by importance
            const string importanceSql = "SELECT StrategicImportance, COUNT(*) FROM BusinessTasks GROUP BY StrategicImportance";
            var importanceCounts = await _databaseService.QueryAsync(importanceSql,
                values => new { Importance = (StrategicImportance)(int)values[0], Count = (int)values[1] });
            
            foreach (var item in importanceCounts)
            {
                analytics.TasksByImportance[item.Importance] = item.Count;
            }
            
            // Get revenue impact
            var revenueImpact = await _databaseService.ExecuteScalarAsync<decimal>(
                "SELECT COALESCE(SUM(RevenueImpact), 0) FROM BusinessTasks WHERE RevenueImpact IS NOT NULL");
            analytics.TotalRevenueImpact = revenueImpact ?? 0m;
            
            // Get average hours
            var averageHours = await _databaseService.ExecuteScalarAsync<double>(
                "SELECT COALESCE(AVG(EstimatedHours), 0) FROM BusinessTasks");
            analytics.AverageHoursPerTask = averageHours ?? 0.0;
            
            return analytics;
        }
        
        private BusinessTask MapBusinessTask(object[] values)
        {
            return new BusinessTask
            {
                Id = values[0]?.ToString() ?? string.Empty,
                Title = values[1]?.ToString() ?? string.Empty,
                Description = values[2]?.ToString() ?? string.Empty,
                DueDate = DateTime.TryParse(values[3]?.ToString(), out var dueDate) ? dueDate : DateTime.Now,
                Category = values[4]?.ToString() ?? string.Empty,
                IsCompleted = Convert.ToInt32(values[5]) == 1,
                Priority = Convert.ToInt32(values[6]),
                CreatedDate = DateTime.TryParse(values[7]?.ToString(), out var createdDate) ? createdDate : DateTime.Now,
                CompletedDate = DateTime.TryParse(values[8]?.ToString(), out var completedDate) ? completedDate : null,
                Status = values[9]?.ToString() ?? "Pending",
                AssignedTo = values[10]?.ToString() ?? string.Empty,
                EstimatedHours = Convert.ToDouble(values[11]),
                ActualHours = Convert.ToDouble(values[12]),
                Tags = values[13]?.ToString() ?? string.Empty,
                BusinessImpact = values[14]?.ToString() ?? "Medium",
                ProjectId = values[15]?.ToString() ?? string.Empty,
                ClientId = values[16]?.ToString() ?? string.Empty,
                TaskType = (BusinessTaskType)Convert.ToInt32(values[17]),
                RevenueImpact = values[18] != null ? Convert.ToDecimal(values[18]) : null,
                StrategicImportance = (StrategicImportance)Convert.ToInt32(values[19])
            };
        }
    }
}