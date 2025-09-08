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
    }
}