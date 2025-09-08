using System;
using System.Collections.ObjectModel;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.ViewModels
{
    public class DashboardViewModel
    {
        public ObservableCollection<BusinessTask> Tasks { get; } = new();
        
        public DashboardViewModel()
        {
            // Add some sample tasks
            Tasks.Add(new BusinessTask 
            { 
                Title = "Create business plan", 
                Description = "Outline the core business strategy",
                DueDate = DateTime.Now.AddDays(7),
                Category = "Planning",
                Priority = 1
            });
            
            Tasks.Add(new BusinessTask 
            { 
                Title = "Research competitors", 
                Description = "Analyze main competitors in the market",
                DueDate = DateTime.Now.AddDays(3),
                Category = "Research",
                Priority = 2
            });
        }
    }
}