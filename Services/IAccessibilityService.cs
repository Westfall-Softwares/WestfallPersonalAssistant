using System;
using System.ComponentModel;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for managing accessibility features throughout the application
    /// </summary>
    public interface IAccessibilityService : INotifyPropertyChanged
    {
        // High Contrast Mode
        bool IsHighContrastMode { get; set; }
        
        // Text Size Scaling
        double TextScalingFactor { get; set; }
        
        // Motion and Animation Settings
        bool ReduceMotion { get; set; }
        
        // Screen Reader Support
        bool ScreenReaderMode { get; set; }
        
        // Focus Management
        bool ShowFocusIndicators { get; set; }
        
        // Keyboard Navigation
        bool EnhancedKeyboardNavigation { get; set; }
        
        // Color Accessibility
        Models.ColorBlindnessType ColorBlindnessAccommodation { get; set; }
        
        // Methods
        void ApplyAccessibilitySettings();
        void ResetToDefaults();
        void AnnounceToScreenReader(string message);
        void LoadSettings();
        void SaveSettings();
        
        // Events
        event EventHandler<AccessibilityChangedEventArgs>? AccessibilitySettingsChanged;
    }
    
    public class AccessibilityChangedEventArgs : EventArgs
    {
        public string? SettingName { get; set; }
        public object? OldValue { get; set; }
        public object? NewValue { get; set; }
    }
}