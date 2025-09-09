using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public class DatabaseBusinessGoalService : IBusinessGoalService
    {
        private readonly IDatabaseService _databaseService;
        
        public event EventHandler<BusinessGoal>? GoalCreated;
        public event EventHandler<BusinessGoal>? GoalUpdated;
        public event EventHandler<BusinessGoal>? GoalCompleted;
        public event EventHandler<string>? GoalDeleted;
        public event EventHandler<GoalProgressEventArgs>? GoalProgressUpdated;
        
        public DatabaseBusinessGoalService(IDatabaseService databaseService)
        {
            _databaseService = databaseService;
        }
        
        public async Task<BusinessGoal[]> GetAllGoalsAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                ORDER BY Priority, TargetDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessGoal);
        }
        
        public async Task<BusinessGoal[]> GetGoalsByTypeAsync(BusinessGoalType goalType)
        {
            const string sql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE GoalType = @p0
                ORDER BY Priority, TargetDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessGoal, (int)goalType);
        }
        
        public async Task<BusinessGoal[]> GetActiveGoalsAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE IsCompleted = 0
                ORDER BY Priority, TargetDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessGoal);
        }
        
        public async Task<BusinessGoal[]> GetCompletedGoalsAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE IsCompleted = 1
                ORDER BY CreatedDate DESC";
            
            return await _databaseService.QueryAsync(sql, MapBusinessGoal);
        }
        
        public async Task<BusinessGoal[]> GetOverdueGoalsAsync()
        {
            const string sql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE IsCompleted = 0 AND TargetDate < @p0
                ORDER BY TargetDate";
            
            return await _databaseService.QueryAsync(sql, MapBusinessGoal, DateTime.Today.ToString("O"));
        }
        
        public async Task<BusinessGoal> CreateGoalAsync(BusinessGoal goal)
        {
            const string sql = @"
                INSERT INTO BusinessGoals (
                    Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                    StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                ) VALUES (
                    @p0, @p1, @p2, @p3, @p4, @p5, @p6, @p7, @p8, @p9, @p10, @p11, @p12
                )";
            
            goal.Id = Guid.NewGuid().ToString();
            goal.CreatedDate = DateTime.Now;
            
            await _databaseService.ExecuteNonQueryAsync(sql,
                goal.Id, goal.Title, goal.Description, goal.TargetValue, goal.CurrentValue,
                goal.Unit, goal.Category, goal.StartDate.ToString("O"), goal.TargetDate.ToString("O"),
                goal.IsCompleted ? 1 : 0, goal.CreatedDate.ToString("O"),
                (int)goal.GoalType, (int)goal.Priority);
            
            GoalCreated?.Invoke(this, goal);
            return goal;
        }
        
        public async Task<BusinessGoal> UpdateGoalAsync(BusinessGoal goal)
        {
            const string sql = @"
                UPDATE BusinessGoals SET 
                    Title = @p1, Description = @p2, TargetValue = @p3, CurrentValue = @p4, 
                    Unit = @p5, Category = @p6, StartDate = @p7, TargetDate = @p8, 
                    IsCompleted = @p9, GoalType = @p10, Priority = @p11
                WHERE Id = @p0";
            
            await _databaseService.ExecuteNonQueryAsync(sql,
                goal.Id, goal.Title, goal.Description, goal.TargetValue, goal.CurrentValue,
                goal.Unit, goal.Category, goal.StartDate.ToString("O"), goal.TargetDate.ToString("O"),
                goal.IsCompleted ? 1 : 0, (int)goal.GoalType, (int)goal.Priority);
            
            GoalUpdated?.Invoke(this, goal);
            return goal;
        }
        
        public async Task<bool> DeleteGoalAsync(string goalId)
        {
            const string sql = "DELETE FROM BusinessGoals WHERE Id = @p0";
            var rowsAffected = await _databaseService.ExecuteNonQueryAsync(sql, goalId);
            
            if (rowsAffected > 0)
            {
                GoalDeleted?.Invoke(this, goalId);
                return true;
            }
            
            return false;
        }
        
        public async Task<bool> CompleteGoalAsync(string goalId)
        {
            // First get the current goal to set CurrentValue = TargetValue
            const string getGoalSql = @"
                SELECT TargetValue FROM BusinessGoals WHERE Id = @p0";
            
            var targetValue = await _databaseService.ExecuteScalarAsync<decimal>(getGoalSql, goalId);
            if (!targetValue.HasValue) return false;
            
            const string sql = @"
                UPDATE BusinessGoals 
                SET IsCompleted = 1, CurrentValue = @p1, CompletedDate = @p2
                WHERE Id = @p0";
            
            var completedDate = DateTime.Now.ToString("O");
            var rowsAffected = await _databaseService.ExecuteNonQueryAsync(sql, goalId, targetValue.Value, completedDate);
            
            if (rowsAffected > 0)
            {
                // Get the updated goal to fire the event
                var goals = await _databaseService.QueryAsync(
                    "SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority FROM BusinessGoals WHERE Id = @p0",
                    MapBusinessGoal, goalId);
                
                if (goals.Length > 0)
                {
                    GoalCompleted?.Invoke(this, goals[0]);
                }
                
                return true;
            }
            
            return false;
        }
        
        public async Task<bool> UpdateGoalProgressAsync(string goalId, decimal currentValue)
        {
            // Get previous value for event
            const string getPreviousValueSql = "SELECT CurrentValue FROM BusinessGoals WHERE Id = @p0";
            var previousValue = await _databaseService.ExecuteScalarAsync<decimal>(getPreviousValueSql, goalId);
            
            const string sql = "UPDATE BusinessGoals SET CurrentValue = @p1 WHERE Id = @p0";
            var rowsAffected = await _databaseService.ExecuteNonQueryAsync(sql, goalId, currentValue);
            
            if (rowsAffected > 0)
            {
                // Get target value to calculate progress
                const string getTargetSql = "SELECT TargetValue FROM BusinessGoals WHERE Id = @p0";
                var targetValue = await _databaseService.ExecuteScalarAsync<decimal>(getTargetSql, goalId);
                
                var progressPercentage = targetValue.HasValue && targetValue.Value > 0 
                    ? Math.Min(100, (double)(currentValue / targetValue.Value) * 100) 
                    : 0;
                
                GoalProgressUpdated?.Invoke(this, new GoalProgressEventArgs(
                    goalId, previousValue ?? 0, currentValue, progressPercentage));
                
                return true;
            }
            
            return false;
        }
        
        public async Task<BusinessGoalAnalytics> GetGoalAnalyticsAsync()
        {
            var analytics = new BusinessGoalAnalytics();
            
            // Get basic counts
            var totalGoals = await _databaseService.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM BusinessGoals");
            analytics.TotalGoals = totalGoals ?? 0;
            
            var activeGoals = await _databaseService.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM BusinessGoals WHERE IsCompleted = 0");
            analytics.ActiveGoals = activeGoals ?? 0;
            
            var completedGoals = await _databaseService.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM BusinessGoals WHERE IsCompleted = 1");
            analytics.CompletedGoals = completedGoals ?? 0;
            
            var overdueGoals = await _databaseService.ExecuteScalarAsync<int>(
                "SELECT COUNT(*) FROM BusinessGoals WHERE IsCompleted = 0 AND TargetDate < @p0",
                DateTime.Today.ToString("O"));
            analytics.OverdueGoals = overdueGoals ?? 0;
            
            // Calculate completion rate
            analytics.CompletionRate = analytics.TotalGoals > 0 
                ? (double)analytics.CompletedGoals / analytics.TotalGoals * 100 
                : 0;
            
            // Calculate average progress for active goals
            var averageProgress = await _databaseService.ExecuteScalarAsync<double>(
                "SELECT AVG(CASE WHEN TargetValue > 0 THEN (CurrentValue * 100.0 / TargetValue) ELSE 0 END) FROM BusinessGoals WHERE IsCompleted = 0");
            analytics.AverageProgress = averageProgress ?? 0;
            
            // Get goals by type
            const string goalTypesSql = "SELECT GoalType, COUNT(*) FROM BusinessGoals GROUP BY GoalType";
            var goalTypeCounts = await _databaseService.QueryAsync(goalTypesSql,
                values => new { Type = (BusinessGoalType)(int)values[0], Count = (int)values[1] });
            
            foreach (var item in goalTypeCounts)
            {
                analytics.GoalsByType[item.Type] = item.Count;
            }
            
            // Get goals by priority
            const string prioritySql = "SELECT Priority, COUNT(*) FROM BusinessGoals GROUP BY Priority";
            var priorityCounts = await _databaseService.QueryAsync(prioritySql,
                values => new { Priority = (GoalPriority)(int)values[0], Count = (int)values[1] });
            
            foreach (var item in priorityCounts)
            {
                analytics.GoalsByPriority[item.Priority] = item.Count;
            }
            
            // Get total values
            var totalTarget = await _databaseService.ExecuteScalarAsync<decimal>(
                "SELECT COALESCE(SUM(TargetValue), 0) FROM BusinessGoals");
            analytics.TotalTargetValue = totalTarget ?? 0;
            
            var totalCurrent = await _databaseService.ExecuteScalarAsync<decimal>(
                "SELECT COALESCE(SUM(CurrentValue), 0) FROM BusinessGoals");
            analytics.TotalCurrentValue = totalCurrent ?? 0;
            
            // Get top performing goals (highest progress %)
            const string topPerformingSql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE IsCompleted = 0 AND TargetValue > 0
                ORDER BY (CurrentValue * 100.0 / TargetValue) DESC
                LIMIT 5";
            
            analytics.TopPerformingGoals = await _databaseService.QueryAsync(topPerformingSql, MapBusinessGoal);
            
            // Get at-risk goals (overdue or low progress)
            const string atRiskSql = @"
                SELECT Id, Title, Description, TargetValue, CurrentValue, Unit, Category, 
                       StartDate, TargetDate, IsCompleted, CreatedDate, GoalType, Priority
                FROM BusinessGoals 
                WHERE IsCompleted = 0 AND (
                    TargetDate < @p0 OR 
                    (TargetValue > 0 AND (CurrentValue * 100.0 / TargetValue) < 25)
                )
                ORDER BY TargetDate
                LIMIT 10";
            
            analytics.AtRiskGoals = await _databaseService.QueryAsync(atRiskSql, MapBusinessGoal, DateTime.Today.ToString("O"));
            
            return analytics;
        }
        
        private BusinessGoal MapBusinessGoal(object[] values)
        {
            return new BusinessGoal
            {
                Id = values[0]?.ToString() ?? string.Empty,
                Title = values[1]?.ToString() ?? string.Empty,
                Description = values[2]?.ToString() ?? string.Empty,
                TargetValue = Convert.ToDecimal(values[3]),
                CurrentValue = Convert.ToDecimal(values[4]),
                Unit = values[5]?.ToString() ?? string.Empty,
                Category = values[6]?.ToString() ?? string.Empty,
                StartDate = DateTime.TryParse(values[7]?.ToString(), out var startDate) ? startDate : DateTime.Now,
                TargetDate = DateTime.TryParse(values[8]?.ToString(), out var targetDate) ? targetDate : DateTime.Now,
                IsCompleted = Convert.ToInt32(values[9]) == 1,
                CreatedDate = DateTime.TryParse(values[10]?.ToString(), out var createdDate) ? createdDate : DateTime.Now,
                GoalType = (BusinessGoalType)Convert.ToInt32(values[11]),
                Priority = (GoalPriority)Convert.ToInt32(values[12])
            };
        }
    }
}