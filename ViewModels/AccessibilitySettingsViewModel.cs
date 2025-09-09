using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.ViewModels
{
    public class AccessibilitySettingsViewModel : INotifyPropertyChanged
    {
        private readonly IAccessibilityService _accessibilityService;
        
        public AccessibilitySettingsViewModel(IAccessibilityService accessibilityService)
        {
            _accessibilityService = accessibilityService ?? throw new ArgumentNullException(nameof(accessibilityService));
            
            // Initialize commands
            ApplyCommand = new RelayCommand(ApplySettings);
            ResetCommand = new RelayCommand(ResetSettings);
            CloseCommand = new RelayCommand(CloseSettings);
            TestAnnouncementCommand = new RelayCommand(TestAnnouncement);
            SetTextSizeCommand = new RelayCommand<object>(SetTextSize);
            ShowHelpCommand = new RelayCommand(ShowHelp);
            
            // Subscribe to service property changes
            _accessibilityService.PropertyChanged += OnAccessibilityServicePropertyChanged;
        }
        
        // Properties that bind to the service
        public bool IsHighContrastMode
        {
            get => _accessibilityService.IsHighContrastMode;
            set => _accessibilityService.IsHighContrastMode = value;
        }
        
        public double TextScalingFactor
        {
            get => _accessibilityService.TextScalingFactor;
            set => _accessibilityService.TextScalingFactor = value;
        }
        
        public bool ReduceMotion
        {
            get => _accessibilityService.ReduceMotion;
            set => _accessibilityService.ReduceMotion = value;
        }
        
        public bool ScreenReaderMode
        {
            get => _accessibilityService.ScreenReaderMode;
            set => _accessibilityService.ScreenReaderMode = value;
        }
        
        public bool ShowFocusIndicators
        {
            get => _accessibilityService.ShowFocusIndicators;
            set => _accessibilityService.ShowFocusIndicators = value;
        }
        
        public bool EnhancedKeyboardNavigation
        {
            get => _accessibilityService.EnhancedKeyboardNavigation;
            set => _accessibilityService.EnhancedKeyboardNavigation = value;
        }
        
        public ColorBlindnessType ColorBlindnessAccommodation
        {
            get => _accessibilityService.ColorBlindnessAccommodation;
            set => _accessibilityService.ColorBlindnessAccommodation = value;
        }
        
        // Commands
        public ICommand ApplyCommand { get; }
        public ICommand ResetCommand { get; }
        public ICommand CloseCommand { get; }
        public ICommand TestAnnouncementCommand { get; }
        public ICommand SetTextSizeCommand { get; }
        public ICommand ShowHelpCommand { get; }
        
        // Events
        public event EventHandler? CloseRequested;
        public event EventHandler<string>? StatusUpdated;
        public event PropertyChangedEventHandler? PropertyChanged;
        
        private void ApplySettings()
        {
            try
            {
                _accessibilityService.ApplyAccessibilitySettings();
                _accessibilityService.AnnounceToScreenReader("Accessibility settings have been applied successfully");
                StatusUpdated?.Invoke(this, "Settings applied successfully");
            }
            catch (Exception ex)
            {
                StatusUpdated?.Invoke(this, $"Error applying settings: {ex.Message}");
            }
        }
        
        private void ResetSettings()
        {
            try
            {
                _accessibilityService.ResetToDefaults();
                _accessibilityService.AnnounceToScreenReader("Accessibility settings have been reset to defaults");
                StatusUpdated?.Invoke(this, "Settings reset to defaults");
            }
            catch (Exception ex)
            {
                StatusUpdated?.Invoke(this, $"Error resetting settings: {ex.Message}");
            }
        }
        
        private void CloseSettings()
        {
            CloseRequested?.Invoke(this, EventArgs.Empty);
        }
        
        private void TestAnnouncement()
        {
            _accessibilityService.AnnounceToScreenReader("This is a test announcement. Screen reader functionality is working correctly.");
            StatusUpdated?.Invoke(this, "Test announcement sent");
        }
        
        private void SetTextSize(object parameter)
        {
            if (parameter is string sizeString && double.TryParse(sizeString, out double size))
            {
                TextScalingFactor = size;
                _accessibilityService.AnnounceToScreenReader($"Text size set to {size:P0}");
            }
        }
        
        private void ShowHelp()
        {
            var helpMessage = @"Accessibility Settings Help:

Visual Accessibility:
- High Contrast Mode: Enhances color contrast for better visibility
- Text Size: Adjusts text size from 80% to 200% of normal
- Reduce Motion: Disables or reduces animations
- Color Blindness: Accommodates different types of color blindness

Keyboard Navigation:
- Enhanced Navigation: Provides additional keyboard shortcuts
- Focus Indicators: Shows visual focus highlights
- Keyboard Shortcuts: Lists available shortcuts

Screen Reader:
- Screen Reader Mode: Optimizes for screen reader usage
- Test Announcement: Verifies screen reader functionality

Use Escape to close this panel, F1 for help.";
            
            _accessibilityService.AnnounceToScreenReader(helpMessage);
            StatusUpdated?.Invoke(this, "Help information announced to screen reader");
        }
        
        private void OnAccessibilityServicePropertyChanged(object sender, PropertyChangedEventArgs e)
        {
            // Forward property change notifications from the service
            OnPropertyChanged(e.PropertyName);
        }
        
        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
    
    // Simple RelayCommand implementation
    public class RelayCommand : ICommand
    {
        private readonly Action _execute;
        private readonly Func<bool>? _canExecute;
        
        public RelayCommand(Action execute, Func<bool>? canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }
        
        public event EventHandler? CanExecuteChanged;
        
        public bool CanExecute(object? parameter) => _canExecute?.Invoke() ?? true;
        
        public void Execute(object? parameter) => _execute();
        
        public void RaiseCanExecuteChanged() => CanExecuteChanged?.Invoke(this, EventArgs.Empty);
    }
    
    public class RelayCommand<T> : ICommand
    {
        private readonly Action<T> _execute;
        private readonly Func<T, bool>? _canExecute;
        
        public RelayCommand(Action<T> execute, Func<T, bool>? canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }
        
        public event EventHandler? CanExecuteChanged;
        
        public bool CanExecute(object? parameter)
        {
            if (parameter is T typedParam)
                return _canExecute?.Invoke(typedParam) ?? true;
            return false;
        }
        
        public void Execute(object? parameter)
        {
            if (parameter is T typedParam)
                _execute(typedParam);
        }
        
        public void RaiseCanExecuteChanged() => CanExecuteChanged?.Invoke(this, EventArgs.Empty);
    }
}