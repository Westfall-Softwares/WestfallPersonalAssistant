using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Avalonia.Media;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for generating and managing application themes
    /// </summary>
    public class ThemeGenerator
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly string _themesDirectory;

        public ThemeGenerator(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _themesDirectory = Path.Combine(_fileSystemService.GetAppDataPath(), "Themes");
        }

        /// <summary>
        /// Generates a theme based on the provided configuration
        /// </summary>
        /// <param name="themeConfig">Theme configuration</param>
        /// <returns>Generated theme dictionary</returns>
        public async Task<Dictionary<string, object>> GenerateThemeAsync(ThemeConfiguration themeConfig)
        {
            if (themeConfig == null)
                throw new ArgumentNullException(nameof(themeConfig));

            try
            {
                var theme = new Dictionary<string, object>();
                
                // Basic color scheme
                theme["Primary"] = themeConfig.PrimaryColor;
                theme["Secondary"] = themeConfig.SecondaryColor;
                theme["Background"] = themeConfig.BackgroundColor;
                theme["Foreground"] = themeConfig.ForegroundColor;
                theme["Accent"] = themeConfig.AccentColor;

                // Generate derived colors
                theme["PrimaryHover"] = AdjustColorBrightness(themeConfig.PrimaryColor, 0.1f);
                theme["PrimaryPressed"] = AdjustColorBrightness(themeConfig.PrimaryColor, -0.1f);
                theme["SecondaryHover"] = AdjustColorBrightness(themeConfig.SecondaryColor, 0.1f);

                // TODO support custom gradients
                // Current theme system only supports solid colors. Future enhancement should:
                // 1. Extend theme JSON schema to allow gradient definitions
                // 2. Generate ResourceDictionary brushes dynamically for gradients
                // 3. Support linear and radial gradient configurations
                // 4. Allow multiple color stops with positions and opacity
                // Example future gradient schema:
                // "gradients": {
                //   "HeaderGradient": {
                //     "type": "linear",
                //     "angle": 90,
                //     "stops": [
                //       { "color": "#FF6B6B", "position": 0.0 },
                //       { "color": "#4ECDC4", "position": 1.0 }
                //     ]
                //   }
                // }

                // Border and shadow colors
                theme["BorderColor"] = themeConfig.BorderColor ?? AdjustColorBrightness(themeConfig.BackgroundColor, -0.2f);
                theme["ShadowColor"] = Color.FromArgb(128, 0, 0, 0).ToString();

                // Text colors for different contexts
                theme["TextPrimary"] = themeConfig.ForegroundColor;
                theme["TextSecondary"] = AdjustColorOpacity(themeConfig.ForegroundColor, 0.7f);
                theme["TextDisabled"] = AdjustColorOpacity(themeConfig.ForegroundColor, 0.4f);

                // Save theme to file if name is provided
                if (!string.IsNullOrWhiteSpace(themeConfig.Name))
                {
                    await SaveThemeAsync(themeConfig.Name, theme);
                }

                return theme;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error generating theme: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Loads a theme from file
        /// </summary>
        /// <param name="themeName">Name of the theme to load</param>
        /// <returns>Theme dictionary or null if not found</returns>
        public async Task<Dictionary<string, object>?> LoadThemeAsync(string themeName)
        {
            if (string.IsNullOrWhiteSpace(themeName))
                return null;

            try
            {
                var themeFilePath = Path.Combine(_themesDirectory, $"{themeName}.json");
                if (!_fileSystemService.FileExists(themeFilePath))
                    return null;

                var themeJson = await _fileSystemService.ReadAllTextAsync(themeFilePath);
                return JsonSerializer.Deserialize<Dictionary<string, object>>(themeJson);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading theme {themeName}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Saves a theme to file
        /// </summary>
        /// <param name="themeName">Name of the theme</param>
        /// <param name="theme">Theme dictionary</param>
        /// <returns>Task representing the save operation</returns>
        public async Task SaveThemeAsync(string themeName, Dictionary<string, object> theme)
        {
            if (string.IsNullOrWhiteSpace(themeName))
                throw new ArgumentException("Theme name cannot be null or empty", nameof(themeName));

            if (theme == null)
                throw new ArgumentNullException(nameof(theme));

            try
            {
                if (!_fileSystemService.DirectoryExists(_themesDirectory))
                {
                    _fileSystemService.CreateDirectory(_themesDirectory);
                }

                var themeFilePath = Path.Combine(_themesDirectory, $"{themeName}.json");
                var themeJson = JsonSerializer.Serialize(theme, new JsonSerializerOptions { WriteIndented = true });
                
                await _fileSystemService.WriteAllTextAsync(themeFilePath, themeJson);
                Console.WriteLine($"Theme saved: {themeName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving theme {themeName}: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Gets list of available theme names
        /// </summary>
        /// <returns>Array of theme names</returns>
        public string[] GetAvailableThemes()
        {
            try
            {
                if (!_fileSystemService.DirectoryExists(_themesDirectory))
                    return Array.Empty<string>();

                var themeFiles = _fileSystemService.GetFiles(_themesDirectory, "*.json");
                var themeNames = new string[themeFiles.Length];
                
                for (int i = 0; i < themeFiles.Length; i++)
                {
                    themeNames[i] = Path.GetFileNameWithoutExtension(themeFiles[i]);
                }

                return themeNames;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting available themes: {ex.Message}");
                return Array.Empty<string>();
            }
        }

        /// <summary>
        /// Adjusts color brightness by the specified factor
        /// </summary>
        /// <param name="colorString">Color as string</param>
        /// <param name="factor">Brightness adjustment factor (-1.0 to 1.0)</param>
        /// <returns>Adjusted color as string</returns>
        private string AdjustColorBrightness(string colorString, float factor)
        {
            try
            {
                if (Color.TryParse(colorString, out var color))
                {
                    var r = Math.Max(0, Math.Min(255, color.R + (int)(255 * factor)));
                    var g = Math.Max(0, Math.Min(255, color.G + (int)(255 * factor)));
                    var b = Math.Max(0, Math.Min(255, color.B + (int)(255 * factor)));
                    
                    return Color.FromArgb(color.A, (byte)r, (byte)g, (byte)b).ToString();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error adjusting color brightness: {ex.Message}");
            }
            
            return colorString; // Return original if adjustment fails
        }

        /// <summary>
        /// Adjusts color opacity by the specified factor
        /// </summary>
        /// <param name="colorString">Color as string</param>
        /// <param name="opacityFactor">Opacity factor (0.0 to 1.0)</param>
        /// <returns>Adjusted color as string</returns>
        private string AdjustColorOpacity(string colorString, float opacityFactor)
        {
            try
            {
                if (Color.TryParse(colorString, out var color))
                {
                    var alpha = (byte)(color.A * Math.Max(0, Math.Min(1, opacityFactor)));
                    return Color.FromArgb(alpha, color.R, color.G, color.B).ToString();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error adjusting color opacity: {ex.Message}");
            }
            
            return colorString; // Return original if adjustment fails
        }
    }

    /// <summary>
    /// Configuration class for theme generation
    /// </summary>
    public class ThemeConfiguration
    {
        public string Name { get; set; } = string.Empty;
        public string PrimaryColor { get; set; } = "#007ACC";
        public string SecondaryColor { get; set; } = "#6C757D";
        public string BackgroundColor { get; set; } = "#FFFFFF";
        public string ForegroundColor { get; set; } = "#212529";
        public string AccentColor { get; set; } = "#FFC107";
        public string? BorderColor { get; set; }
    }
}