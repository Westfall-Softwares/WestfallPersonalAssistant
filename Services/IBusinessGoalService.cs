using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public interface IBusinessGoalService
    {
        Task<BusinessGoal[]> GetAllGoalsAsync();
        Task<BusinessGoal[]> GetGoalsByTypeAsync(BusinessGoalType goalType);
        Task<BusinessGoal[]> GetActiveGoalsAsync();
        Task<BusinessGoal[]> GetCompletedGoalsAsync();
        Task<BusinessGoal[]> GetOverdueGoalsAsync();
        Task<BusinessGoal> CreateGoalAsync(BusinessGoal goal);
        Task<BusinessGoal> UpdateGoalAsync(BusinessGoal goal);
        Task<bool> DeleteGoalAsync(string goalId);
        Task<bool> CompleteGoalAsync(string goalId);
        Task<bool> UpdateGoalProgressAsync(string goalId, decimal currentValue);
        Task<BusinessGoalAnalytics> GetGoalAnalyticsAsync();
        
        event EventHandler<BusinessGoal>? GoalCreated;
        event EventHandler<BusinessGoal>? GoalUpdated;
        event EventHandler<BusinessGoal>? GoalCompleted;
        event EventHandler<string>? GoalDeleted;
        event EventHandler<GoalProgressEventArgs>? GoalProgressUpdated;
    }
    
    public class BusinessGoalAnalytics
    {
        public int TotalGoals { get; set; }
        public int ActiveGoals { get; set; }
        public int CompletedGoals { get; set; }
        public int OverdueGoals { get; set; }
        public double AverageProgress { get; set; }
        public double CompletionRate { get; set; }
        public Dictionary<BusinessGoalType, int> GoalsByType { get; set; } = new();
        public Dictionary<GoalPriority, int> GoalsByPriority { get; set; } = new();
        public decimal TotalTargetValue { get; set; }
        public decimal TotalCurrentValue { get; set; }
        public BusinessGoal[] TopPerformingGoals { get; set; } = Array.Empty<BusinessGoal>();
        public BusinessGoal[] AtRiskGoals { get; set; } = Array.Empty<BusinessGoal>();
    }
    
    public class GoalProgressEventArgs : EventArgs
    {
        public string GoalId { get; }
        public decimal PreviousValue { get; }
        public decimal NewValue { get; }
        public double ProgressPercentage { get; }
        
        public GoalProgressEventArgs(string goalId, decimal previousValue, decimal newValue, double progressPercentage)
        {
            GoalId = goalId;
            PreviousValue = previousValue;
            NewValue = newValue;
            ProgressPercentage = progressPercentage;
        }
    }
}