using System;

namespace WestfallPersonalAssistant.Models
{
    public class BusinessGoal
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Title { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public decimal TargetValue { get; set; }
        public decimal CurrentValue { get; set; }
        public string Unit { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public DateTime StartDate { get; set; } = DateTime.Now;
        public DateTime TargetDate { get; set; }
        public bool IsCompleted { get; set; }
        public DateTime CreatedDate { get; set; } = DateTime.Now;
        public DateTime? CompletedDate { get; set; }
        
        /// <summary>
        /// Business goal type categorization
        /// </summary>
        public BusinessGoalType GoalType { get; set; } = BusinessGoalType.Revenue;
        
        /// <summary>
        /// Priority level for business goals
        /// </summary>
        public GoalPriority Priority { get; set; } = GoalPriority.Medium;
        
        /// <summary>
        /// Current progress as percentage (0-100)
        /// </summary>
        public double ProgressPercentage 
        { 
            get 
            {
                if (TargetValue == 0) return 0;
                return Math.Min(100, (double)(CurrentValue / TargetValue) * 100);
            }
        }
        
        /// <summary>
        /// Days remaining to target date
        /// </summary>
        public int DaysRemaining
        {
            get
            {
                return (TargetDate - DateTime.Today).Days;
            }
        }
        
        /// <summary>
        /// Whether the goal is overdue
        /// </summary>
        public bool IsOverdue
        {
            get
            {
                return !IsCompleted && DateTime.Today > TargetDate;
            }
        }
    }
    
    public enum BusinessGoalType
    {
        Revenue,        // Revenue targets
        Customers,      // Customer acquisition
        Sales,          // Sales volume
        Marketing,      // Marketing metrics (CTR, conversions, etc.)
        Operations,     // Operational efficiency
        Growth,         // Business growth metrics
        Cost,           // Cost reduction targets
        Quality,        // Quality improvement
        Innovation,     // Innovation and development
        Team            // Team and HR goals
    }
    
    public enum GoalPriority
    {
        Critical,   // Must achieve for business survival
        High,       // Important for significant growth
        Medium,     // Standard business objectives
        Low         // Nice-to-have aspirational goals
    }
}