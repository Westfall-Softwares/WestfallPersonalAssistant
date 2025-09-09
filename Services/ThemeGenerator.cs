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

                // Add gradient support
                if (themeConfig.Gradients != null && themeConfig.Gradients.Count > 0)
                {
                    foreach (var gradientPair in themeConfig.Gradients)
                    {
                        theme[gradientPair.Key] = ConvertGradientToString(gradientPair.Value);
                    }
                }

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
        /// Generates a theme from a Theme object (with full gradient support)
        /// </summary>
        /// <param name="theme">Theme object</param>
        /// <returns>Generated theme dictionary with gradients</returns>
        public async Task<Dictionary<string, object>> GenerateThemeFromObjectAsync(Theme theme)
        {
            if (theme == null)
                throw new ArgumentNullException(nameof(theme));

            try
            {
                var themeDict = new Dictionary<string, object>();

                // Add all solid colors
                foreach (var colorPair in theme.Colors)
                {
                    themeDict[colorPair.Key] = colorPair.Value;
                }

                // Add gradients with special prefix or conversion
                foreach (var gradientPair in theme.Gradients)
                {
                    themeDict[$"Gradient_{gradientPair.Key}"] = ConvertGradientToString(gradientPair.Value);
                }

                // Save theme to file
                if (!string.IsNullOrWhiteSpace(theme.Name))
                {
                    await SaveThemeObjectAsync(theme);
                }

                return themeDict;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error generating theme from object: {ex.Message}");
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

        /// <summary>
        /// Converts a gradient definition to a string representation
        /// In a real implementation, this would generate appropriate CSS or XAML gradient syntax
        /// </summary>
        private string ConvertGradientToString(GradientDefinition gradient)
        {
            if (gradient.Type == GradientType.Linear)
            {
                var stops = string.Join(", ", gradient.Stops.Select(s => $"{s.Color} {s.Position:P0}"));
                return $"linear-gradient({gradient.Angle}deg, {stops})";
            }
            else if (gradient.Type == GradientType.Radial)
            {
                var stops = string.Join(", ", gradient.Stops.Select(s => $"{s.Color} {s.Position:P0}"));
                return $"radial-gradient(ellipse {gradient.RadiusX:P0} {gradient.RadiusY:P0} at {gradient.Center.X:P0} {gradient.Center.Y:P0}, {stops})";
            }

            return "none";
        }

        /// <summary>
        /// Creates a linear gradient definition
        /// </summary>
        public static GradientDefinition CreateLinearGradient(string name, double angle, params (string color, double position)[] stops)
        {
            var gradient = new GradientDefinition
            {
                Name = name,
                Type = GradientType.Linear,
                Angle = angle
            };

            foreach (var (color, position) in stops)
            {
                if (Color.TryParse(color, out var parsedColor))
                {
                    gradient.Stops.Add(new GradientStop(parsedColor, position));
                }
            }

            return gradient;
        }

        /// <summary>
        /// Creates a radial gradient definition
        /// </summary>
        public static GradientDefinition CreateRadialGradient(string name, Point center, double radiusX, double radiusY, params (string color, double position)[] stops)
        {
            var gradient = new GradientDefinition
            {
                Name = name,
                Type = GradientType.Radial,
                Center = center,
                RadiusX = radiusX,
                RadiusY = radiusY
            };

            foreach (var (color, position) in stops)
            {
                if (Color.TryParse(color, out var parsedColor))
                {
                    gradient.Stops.Add(new GradientStop(parsedColor, position));
                }
            }

            return gradient;
        }

        /// <summary>
        /// Loads a theme object with gradient support
        /// </summary>
        /// <param name="themeName">Name of the theme to load</param>
        /// <returns>Theme object or null if not found</returns>
        public async Task<Theme?> LoadThemeObjectAsync(string themeName)
        {
            if (string.IsNullOrWhiteSpace(themeName))
                return null;

            try
            {
                var themeFilePath = Path.Combine(_themesDirectory, $"{themeName}.json");
                if (!_fileSystemService.FileExists(themeFilePath))
                    return null;

                var themeJson = await _fileSystemService.ReadAllTextAsync(themeFilePath);
                return JsonSerializer.Deserialize<Theme>(themeJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading theme object {themeName}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Saves a theme object with gradient support
        /// </summary>
        /// <param name="theme">Theme object to save</param>
        /// <returns>Task representing the save operation</returns>
        public async Task SaveThemeObjectAsync(Theme theme)
        {
            if (theme == null)
                throw new ArgumentNullException(nameof(theme));

            if (string.IsNullOrWhiteSpace(theme.Name))
                throw new ArgumentException("Theme name cannot be null or empty", nameof(theme));

            try
            {
                if (!_fileSystemService.DirectoryExists(_themesDirectory))
                {
                    _fileSystemService.CreateDirectory(_themesDirectory);
                }

                theme.UpdatedAt = DateTime.UtcNow;
                var themeFilePath = Path.Combine(_themesDirectory, $"{theme.Name}.json");
                var themeJson = JsonSerializer.Serialize(theme, new JsonSerializerOptions 
                { 
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });
                
                await _fileSystemService.WriteAllTextAsync(themeFilePath, themeJson);
                Console.WriteLine($"Theme with gradients saved: {theme.Name}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving theme object {theme.Name}: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Creates a sample gradient theme for demonstration
        /// </summary>
        public async Task<Theme> CreateSampleGradientThemeAsync()
        {
            var theme = new Theme
            {
                Name = "Ocean Breeze",
                Description = "A calming theme with ocean-inspired gradients",
                Author = "Westfall Assistant",
                Colors = new Dictionary<string, string>
                {
                    { "Primary", "#3498db" },
                    { "Secondary", "#2ecc71" },
                    { "Background", "#ecf0f1" },
                    { "Foreground", "#2c3e50" },
                    { "Accent", "#e74c3c" }
                },
                Gradients = new Dictionary<string, GradientDefinition>
                {
                    {
                        "HeaderBackground",
                        CreateLinearGradient("HeaderBackground", 45, 
                            ("#3498db", 0.0), 
                            ("#2ecc71", 1.0))
                    },
                    {
                        "SidebarBackground",
                        CreateRadialGradient("SidebarBackground", new Point(0.5, 0.5), 0.8, 0.8,
                            ("#3498db", 0.0),
                            ("#2c3e50", 1.0))
                    },
                    {
                        "ButtonGradient",
                        CreateLinearGradient("ButtonGradient", 90,
                            ("#e74c3c", 0.0),
                            ("#c0392b", 1.0))
                    }
                }
            };

            await SaveThemeObjectAsync(theme);
            return theme;
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
        public Dictionary<string, GradientDefinition>? Gradients { get; set; }
    }

    /// <summary>
    /// Gradient type enumeration
    /// </summary>
    public enum GradientType
    {
        Linear,
        Radial
    }

    /// <summary>
    /// Represents a gradient stop with color and position
    /// </summary>
    public class GradientStop
    {
        public Color Color { get; set; }
        public double Position { get; set; } // 0.0 to 1.0

        public GradientStop() { }

        public GradientStop(Color color, double position)
        {
            Color = color;
            Position = Math.Max(0.0, Math.Min(1.0, position));
        }
    }

    /// <summary>
    /// Represents a gradient definition for themes
    /// </summary>
    public class GradientDefinition
    {
        public string Name { get; set; } = string.Empty;
        public GradientType Type { get; set; } = GradientType.Linear;
        public List<GradientStop> Stops { get; set; } = new();

        // For Linear gradients
        public double Angle { get; set; } = 0.0; // In degrees, 0-360

        // For Radial gradients
        public Point Center { get; set; } = new Point(0.5, 0.5); // 0.0 to 1.0 relative positioning
        public double RadiusX { get; set; } = 0.5; // 0.0 to 1.0 relative to width
        public double RadiusY { get; set; } = 0.5; // 0.0 to 1.0 relative to height
    }

    /// <summary>
    /// Simple point structure for gradient centers
    /// </summary>
    public struct Point
    {
        public double X { get; set; }
        public double Y { get; set; }

        public Point(double x, double y)
        {
            X = x;
            Y = y;
        }
    }

    /// <summary>
    /// Extended theme class with gradient support
    /// </summary>
    public class Theme
    {
        public string Name { get; set; } = string.Empty;
        public string Version { get; set; } = "1.0";
        public Dictionary<string, string> Colors { get; set; } = new();
        public Dictionary<string, GradientDefinition> Gradients { get; set; } = new();
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
        public string Description { get; set; } = string.Empty;
        public string Author { get; set; } = string.Empty;
    }
}