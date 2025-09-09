using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Implementation of accessibility service with settings persistence
    /// </summary>
    public class AccessibilityService : IAccessibilityService, INotifyPropertyChanged
    {
        private bool _isHighContrastMode;
        private double _textScalingFactor = 1.0;
        private bool _reduceMotion;
        private bool _screenReaderMode;
        private bool _showFocusIndicators = true;
        private bool _enhancedKeyboardNavigation = true;
        private ColorBlindnessType _colorBlindnessAccommodation = ColorBlindnessType.None;
        
        private readonly ISettingsManager _settingsManager;
        
        public AccessibilityService(ISettingsManager settingsManager)
        {
            _settingsManager = settingsManager;
            LoadSettings();
        }
        
        public bool IsHighContrastMode
        {
            get => _isHighContrastMode;
            set => SetProperty(ref _isHighContrastMode, value);
        }
        
        public double TextScalingFactor
        {
            get => _textScalingFactor;
            set => SetProperty(ref _textScalingFactor, Math.Max(0.8, Math.Min(2.0, value)));
        }
        
        public bool ReduceMotion
        {
            get => _reduceMotion;
            set => SetProperty(ref _reduceMotion, value);
        }
        
        public bool ScreenReaderMode
        {
            get => _screenReaderMode;
            set => SetProperty(ref _screenReaderMode, value);
        }
        
        public bool ShowFocusIndicators
        {
            get => _showFocusIndicators;
            set => SetProperty(ref _showFocusIndicators, value);
        }
        
        public bool EnhancedKeyboardNavigation
        {
            get => _enhancedKeyboardNavigation;
            set => SetProperty(ref _enhancedKeyboardNavigation, value);
        }
        
        public ColorBlindnessType ColorBlindnessAccommodation
        {
            get => _colorBlindnessAccommodation;
            set => SetProperty(ref _colorBlindnessAccommodation, value);
        }
        
        public void ApplyAccessibilitySettings()
        {
            // Apply settings to the application
            AccessibilitySettingsChanged?.Invoke(this, new AccessibilityChangedEventArgs
            {
                SettingName = "All",
                OldValue = null,
                NewValue = "Applied"
            });
        }
        
        public void ResetToDefaults()
        {
            IsHighContrastMode = false;
            TextScalingFactor = 1.0;
            ReduceMotion = false;
            ScreenReaderMode = false;
            ShowFocusIndicators = true;
            EnhancedKeyboardNavigation = true;
            ColorBlindnessAccommodation = ColorBlindnessType.None;
            
            SaveSettings();
        }
        
        public void AnnounceToScreenReader(string message)
        {
            if (string.IsNullOrWhiteSpace(message) || !ScreenReaderMode)
                return;
                
            // Implementation would depend on platform-specific screen reader APIs
            // For now, we'll use a simple approach that works with most screen readers
            OnScreenReaderAnnouncement?.Invoke(message);
        }
        
        public void LoadSettings()
        {
            try
            {
                var settings = _settingsManager.GetCurrentSettings();
                if (settings?.AccessibilitySettings != null)
                {
                    var accessibilitySettings = settings.AccessibilitySettings;
                    _isHighContrastMode = accessibilitySettings.IsHighContrastMode;
                    _textScalingFactor = accessibilitySettings.TextScalingFactor;
                    _reduceMotion = accessibilitySettings.ReduceMotion;
                    _screenReaderMode = accessibilitySettings.ScreenReaderMode;
                    _showFocusIndicators = accessibilitySettings.ShowFocusIndicators;
                    _enhancedKeyboardNavigation = accessibilitySettings.EnhancedKeyboardNavigation;
                    _colorBlindnessAccommodation = accessibilitySettings.ColorBlindnessAccommodation;
                }
            }
            catch (Exception ex)
            {
                // Log error and use defaults
                Console.WriteLine($"Error loading accessibility settings: {ex.Message}");
            }
        }
        
        public void SaveSettings()
        {
            try
            {
                var currentSettings = _settingsManager.GetCurrentSettings();
                if (currentSettings.AccessibilitySettings == null)
                    currentSettings.AccessibilitySettings = new AccessibilitySettings();
                
                currentSettings.AccessibilitySettings.IsHighContrastMode = _isHighContrastMode;
                currentSettings.AccessibilitySettings.TextScalingFactor = _textScalingFactor;
                currentSettings.AccessibilitySettings.ReduceMotion = _reduceMotion;
                currentSettings.AccessibilitySettings.ScreenReaderMode = _screenReaderMode;
                currentSettings.AccessibilitySettings.ShowFocusIndicators = _showFocusIndicators;
                currentSettings.AccessibilitySettings.EnhancedKeyboardNavigation = _enhancedKeyboardNavigation;
                currentSettings.AccessibilitySettings.ColorBlindnessAccommodation = _colorBlindnessAccommodation;
                
                Task.Run(async () => await _settingsManager.SaveSettingsAsync(currentSettings));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving accessibility settings: {ex.Message}");
            }
        }
        
        public event EventHandler<AccessibilityChangedEventArgs>? AccessibilitySettingsChanged;
        public event Action<string>? OnScreenReaderAnnouncement;
        public event PropertyChangedEventHandler? PropertyChanged;
        
        private void SetProperty<T>(ref T field, T value, [CallerMemberName] string propertyName = null)
        {
            if (!Equals(field, value))
            {
                var oldValue = field;
                field = value;
                OnPropertyChanged(propertyName);
                
                AccessibilitySettingsChanged?.Invoke(this, new AccessibilityChangedEventArgs
                {
                    SettingName = propertyName,
                    OldValue = oldValue,
                    NewValue = value
                });
                
                SaveSettings();
            }
        }
        
        private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}