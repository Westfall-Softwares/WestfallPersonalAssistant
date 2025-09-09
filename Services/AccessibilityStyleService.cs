using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Styling;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for applying accessibility-related styling and visual enhancements
    /// </summary>
    public interface IAccessibilityStyleService
    {
        void ApplyHighContrastMode(bool enabled);
        void ApplyTextScaling(double factor);
        void ApplyReducedMotion(bool enabled);
        void ApplyEnhancedFocusIndicators(bool enabled);
        void ApplyColorBlindnessAccommodations(Models.ColorBlindnessType type);
    }

    /// <summary>
    /// Implementation of accessibility styling service
    /// </summary>
    public class AccessibilityStyleService : IAccessibilityStyleService
    {
        private readonly Application _application;

        public AccessibilityStyleService()
        {
            _application = Application.Current ?? throw new InvalidOperationException("Application not available");
        }

        public void ApplyHighContrastMode(bool enabled)
        {
            try
            {
                if (enabled)
                {
                    // Apply high contrast colors
                    ApplyHighContrastResources();
                }
                else
                {
                    // Restore normal colors
                    RestoreNormalResources();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying high contrast mode: {ex.Message}");
            }
        }

        public void ApplyTextScaling(double factor)
        {
            try
            {
                // Clamp factor to reasonable range
                factor = Math.Max(0.8, Math.Min(2.0, factor));

                // Apply text scaling to application resources
                if (_application.Resources.ContainsKey("DefaultFontSize"))
                {
                    var baseFontSize = 14.0; // Default base font size
                    _application.Resources["DefaultFontSize"] = baseFontSize * factor;
                }
                
                // Apply to various text elements
                var textSizes = new Dictionary<string, double>
                {
                    ["SmallFontSize"] = 12.0 * factor,
                    ["MediumFontSize"] = 14.0 * factor,
                    ["LargeFontSize"] = 18.0 * factor,
                    ["XLargeFontSize"] = 24.0 * factor,
                    ["HeadingFontSize"] = 28.0 * factor
                };

                foreach (var (key, size) in textSizes)
                {
                    _application.Resources[key] = size;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying text scaling: {ex.Message}");
            }
        }

        public void ApplyReducedMotion(bool enabled)
        {
            try
            {
                if (enabled)
                {
                    // Disable or reduce animations
                    _application.Resources["AnimationDuration"] = TimeSpan.Zero;
                    _application.Resources["TransitionDuration"] = TimeSpan.Zero;
                }
                else
                {
                    // Restore normal animation timings
                    _application.Resources["AnimationDuration"] = TimeSpan.FromMilliseconds(250);
                    _application.Resources["TransitionDuration"] = TimeSpan.FromMilliseconds(150);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying reduced motion: {ex.Message}");
            }
        }

        public void ApplyEnhancedFocusIndicators(bool enabled)
        {
            try
            {
                if (enabled)
                {
                    // Apply enhanced focus indicators
                    _application.Resources["FocusIndicatorBrush"] = new SolidColorBrush(Colors.Orange);
                    _application.Resources["FocusIndicatorThickness"] = new Thickness(3);
                    _application.Resources["FocusIndicatorCornerRadius"] = new CornerRadius(2);
                    _application.Resources["FocusIndicatorOpacity"] = 1.0;
                }
                else
                {
                    // Use default focus indicators
                    _application.Resources["FocusIndicatorBrush"] = new SolidColorBrush(Colors.DodgerBlue);
                    _application.Resources["FocusIndicatorThickness"] = new Thickness(1);
                    _application.Resources["FocusIndicatorCornerRadius"] = new CornerRadius(0);
                    _application.Resources["FocusIndicatorOpacity"] = 0.8;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying focus indicators: {ex.Message}");
            }
        }

        public void ApplyColorBlindnessAccommodations(Models.ColorBlindnessType type)
        {
            try
            {
                switch (type)
                {
                    case Models.ColorBlindnessType.Deuteranopia:
                        ApplyDeuteranopiaPalette();
                        break;
                    case Models.ColorBlindnessType.Protanopia:
                        ApplyProtanopiaPalette();
                        break;
                    case Models.ColorBlindnessType.Tritanopia:
                        ApplyTritanopiaPalette();
                        break;
                    case Models.ColorBlindnessType.None:
                    default:
                        RestoreNormalPalette();
                        break;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying color blindness accommodations: {ex.Message}");
            }
        }

        private void ApplyHighContrastResources()
        {
            var resources = new Dictionary<string, object>
            {
                ["WindowBackgroundBrush"] = new SolidColorBrush(Colors.Black),
                ["WindowForegroundBrush"] = new SolidColorBrush(Colors.White),
                ["ButtonBackgroundBrush"] = new SolidColorBrush(Colors.White),
                ["ButtonForegroundBrush"] = new SolidColorBrush(Colors.Black),
                ["BorderBrush"] = new SolidColorBrush(Colors.White),
                ["SuccessBrush"] = new SolidColorBrush(Colors.Lime),
                ["ErrorBrush"] = new SolidColorBrush(Colors.Red),
                ["WarningBrush"] = new SolidColorBrush(Colors.Yellow)
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }

        private void RestoreNormalResources()
        {
            var resources = new Dictionary<string, object>
            {
                ["WindowBackgroundBrush"] = new SolidColorBrush(Colors.White),
                ["WindowForegroundBrush"] = new SolidColorBrush(Colors.Black),
                ["ButtonBackgroundBrush"] = new SolidColorBrush(Color.Parse("#F0F0F0")),
                ["ButtonForegroundBrush"] = new SolidColorBrush(Colors.Black),
                ["BorderBrush"] = new SolidColorBrush(Color.Parse("#CCCCCC")),
                ["SuccessBrush"] = new SolidColorBrush(Color.Parse("#4CAF50")),
                ["ErrorBrush"] = new SolidColorBrush(Color.Parse("#F44336")),
                ["WarningBrush"] = new SolidColorBrush(Color.Parse("#FF9800"))
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }

        private void ApplyDeuteranopiaPalette()
        {
            // Green-blind friendly palette
            var resources = new Dictionary<string, object>
            {
                ["SuccessBrush"] = new SolidColorBrush(Color.Parse("#0066CC")), // Blue instead of green
                ["WarningBrush"] = new SolidColorBrush(Color.Parse("#FF6600")), // Orange
                ["InfoBrush"] = new SolidColorBrush(Color.Parse("#9933CC"))     // Purple
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }

        private void ApplyProtanopiaPalette()
        {
            // Red-blind friendly palette
            var resources = new Dictionary<string, object>
            {
                ["ErrorBrush"] = new SolidColorBrush(Color.Parse("#0066CC")),   // Blue instead of red
                ["WarningBrush"] = new SolidColorBrush(Color.Parse("#FF6600")), // Orange
                ["InfoBrush"] = new SolidColorBrush(Color.Parse("#9933CC"))     // Purple
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }

        private void ApplyTritanopiaPalette()
        {
            // Blue-blind friendly palette
            var resources = new Dictionary<string, object>
            {
                ["InfoBrush"] = new SolidColorBrush(Color.Parse("#009900")),    // Green instead of blue
                ["ErrorBrush"] = new SolidColorBrush(Color.Parse("#CC0000")),   // Red
                ["WarningBrush"] = new SolidColorBrush(Color.Parse("#FF6600"))  // Orange
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }

        private void RestoreNormalPalette()
        {
            var resources = new Dictionary<string, object>
            {
                ["SuccessBrush"] = new SolidColorBrush(Color.Parse("#4CAF50")),
                ["ErrorBrush"] = new SolidColorBrush(Color.Parse("#F44336")),
                ["WarningBrush"] = new SolidColorBrush(Color.Parse("#FF9800")),
                ["InfoBrush"] = new SolidColorBrush(Color.Parse("#2196F3"))
            };

            foreach (var (key, value) in resources)
            {
                _application.Resources[key] = value;
            }
        }
    }
}