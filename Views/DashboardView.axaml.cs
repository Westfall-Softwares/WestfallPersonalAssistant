using Avalonia.Controls;
using WestfallPersonalAssistant.ViewModels;

namespace WestfallPersonalAssistant.Views
{
    public partial class DashboardView : UserControl
    {
        public DashboardView()
        {
            InitializeComponent();
            DataContext = new DashboardViewModel();
            
            // Bind the tasks to the ItemsControl
            var tasksList = this.FindControl<ItemsControl>("TasksList");
            if (tasksList != null && DataContext is DashboardViewModel viewModel)
            {
                tasksList.ItemsSource = viewModel.Tasks;
            }
        }
    }
}