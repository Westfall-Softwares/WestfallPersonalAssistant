using Avalonia.Controls;
using Avalonia.Interactivity;
using System;
using System.Threading.Tasks;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Views
{
    public partial class PackManagementView : UserControl
    {
        public PackManagementView()
        {
            InitializeComponent();
        }
        
        private async void OnVerifyOrderClick(object? sender, RoutedEventArgs e)
        {
            var orderTextBox = this.FindControl<TextBox>("OrderNumberTextBox");
            var statusTextBlock = this.FindControl<TextBlock>("StatusTextBlock");
            var verifyButton = this.FindControl<Button>("VerifyButton");
            
            if (orderTextBox == null || statusTextBlock == null || verifyButton == null) return;
            
            var orderNumber = orderTextBox.Text?.Trim();
            if (string.IsNullOrEmpty(orderNumber))
            {
                statusTextBlock.Text = "Please enter an order number";
                statusTextBlock.Foreground = Avalonia.Media.Brushes.Red;
                return;
            }
            
            try
            {
                verifyButton.IsEnabled = false;
                statusTextBlock.Text = "Verifying order...";
                statusTextBlock.Foreground = Avalonia.Media.Brushes.Blue;
                
                var packManager = TailorPackManager.Instance;
                var success = await packManager.VerifyAndActivatePackAsync(orderNumber);
                
                if (success)
                {
                    statusTextBlock.Text = "✅ Order verified and pack activated successfully!";
                    statusTextBlock.Foreground = Avalonia.Media.Brushes.Green;
                    orderTextBox.Text = "";
                    
                    // Refresh the UI to show the newly activated pack
                    RefreshPackList();
                }
                else
                {
                    statusTextBlock.Text = "❌ Order verification failed. Please check your order number.";
                    statusTextBlock.Foreground = Avalonia.Media.Brushes.Red;
                }
            }
            catch (Exception ex)
            {
                statusTextBlock.Text = $"Error: {ex.Message}";
                statusTextBlock.Foreground = Avalonia.Media.Brushes.Red;
            }
            finally
            {
                verifyButton.IsEnabled = true;
            }
        }
        
        private void RefreshPackList()
        {
            try
            {
                var packManager = TailorPackManager.Instance;
                var installedPacks = packManager.GetInstalledPacks();
                
                // Update the UI to reflect newly installed/activated packs
                Console.WriteLine($"Refreshed pack list: {installedPacks.Length} packs installed");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error refreshing pack list: {ex.Message}");
            }
        }
    }
}