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
        private readonly IAccessibilityStyleService? _styleService;
        
        public AccessibilityService(ISettingsManager settingsManager, IAccessibilityStyleService? styleService = null)
        {
            _settingsManager = settingsManager;
            _styleService = styleService;
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
            try
            {
                _styleService?.ApplyHighContrastMode(_isHighContrastMode);
                _styleService?.ApplyTextScaling(_textScalingFactor);
                _styleService?.ApplyReducedMotion(_reduceMotion);
                _styleService?.ApplyEnhancedFocusIndicators(_showFocusIndicators);
                _styleService?.ApplyColorBlindnessAccommodations(_colorBlindnessAccommodation);
                
                AccessibilitySettingsChanged?.Invoke(this, new AccessibilityChangedEventArgs
                {
                    SettingName = "All",
                    OldValue = null,
                    NewValue = "Applied"
                });
                
                AnnounceToScreenReader("Accessibility settings have been applied successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying accessibility settings: {ex.Message}");
                AnnounceToScreenReader("Error applying accessibility settings");
            }
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
                
            // Sanitize the message to prevent issues
            var sanitizedMessage = message.Replace("<", "").Replace(">", "").Trim();
            
            if (string.IsNullOrWhiteSpace(sanitizedMessage))
                return;
                
            // Implementation for cross-platform screen reader support
            try
            {
                // Primary announcement mechanism
                OnScreenReaderAnnouncement?.Invoke(sanitizedMessage);
                
                // Additional platform-specific announcements could be added here
                // For example, on Windows: use SAPI or UI Automation
                // On macOS: use NSAccessibility
                // On Linux: use AT-SPI
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error announcing to screen reader: {ex.Message}");
            }
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
                
                // Apply style changes immediately
                try
                {
                    switch (propertyName)
                    {
                        case nameof(IsHighContrastMode):
                            _styleService?.ApplyHighContrastMode(_isHighContrastMode);
                            break;
                        case nameof(TextScalingFactor):
                            _styleService?.ApplyTextScaling(_textScalingFactor);
                            break;
                        case nameof(ReduceMotion):
                            _styleService?.ApplyReducedMotion(_reduceMotion);
                            break;
                        case nameof(ShowFocusIndicators):
                            _styleService?.ApplyEnhancedFocusIndicators(_showFocusIndicators);
                            break;
                        case nameof(ColorBlindnessAccommodation):
                            _styleService?.ApplyColorBlindnessAccommodations(_colorBlindnessAccommodation);
                            break;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error applying style for {propertyName}: {ex.Message}");
                }
                
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