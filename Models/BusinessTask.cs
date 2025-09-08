using System;

namespace WestfallPersonalAssistant.Models
{
    public class BusinessTask
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Title { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public DateTime DueDate { get; set; }
        public string Category { get; set; } = string.Empty;
        public bool IsCompleted { get; set; }
        public int Priority { get; set; }
        public DateTime CreatedDate { get; set; } = DateTime.Now;
        public DateTime? CompletedDate { get; set; }
        public string Status { get; set; } = "Pending";
        public string AssignedTo { get; set; } = string.Empty;
        public double EstimatedHours { get; set; }
        public double ActualHours { get; set; }
        public string Tags { get; set; } = string.Empty;
        public string BusinessImpact { get; set; } = "Medium";
        public string ProjectId { get; set; } = string.Empty;
        public string ClientId { get; set; } = string.Empty;
        
        /// <summary>
        /// Business-specific categorization for tasks
        /// </summary>
        public BusinessTaskType TaskType { get; set; } = BusinessTaskType.Operations;
        
        /// <summary>
        /// Revenue impact of completing this task
        /// </summary>
        public decimal? RevenueImpact { get; set; }
        
        /// <summary>
        /// Strategic importance for business growth
        /// </summary>
        public StrategicImportance StrategicImportance { get; set; } = StrategicImportance.Medium;
    }
    
    public enum BusinessTaskType
    {
        Strategic,      // Long-term planning, strategy development
        Marketing,      // Marketing campaigns, content creation
        Sales,          // Lead generation, customer outreach
        Operations,     // Daily business operations
        Finance,        // Budgeting, invoicing, financial planning
        CustomerService, // Customer support, relationship management
        ProductDevelopment, // Product improvements, new features
        Compliance,     // Legal, regulatory, compliance tasks
        Research,       // Market research, competitor analysis
        Administrative  // General admin tasks
    }
    
    public enum StrategicImportance
    {
        Critical,   // Business-critical, urgent
        High,       // Important for growth
        Medium,     // Standard business tasks
        Low         // Nice-to-have, can be delayed
    }
}