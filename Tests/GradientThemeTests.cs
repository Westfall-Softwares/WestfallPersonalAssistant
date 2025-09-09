using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;
using Avalonia.Media;

namespace WestfallPersonalAssistant.Tests
{
    public class GradientThemeTests
    {
        [Fact]
        public void GradientDefinition_LinearGradient_ShouldCreateCorrectly()
        {
            // Arrange & Act
            var gradient = ThemeGenerator.CreateLinearGradient("TestGradient", 45, 
                ("#FF0000", 0.0), 
                ("#0000FF", 1.0));

            // Assert
            Assert.Equal("TestGradient", gradient.Name);
            Assert.Equal(GradientType.Linear, gradient.Type);
            Assert.Equal(45.0, gradient.Angle);
            Assert.Equal(2, gradient.Stops.Count);
        }

        [Fact]
        public void GradientDefinition_RadialGradient_ShouldCreateCorrectly()
        {
            // Arrange & Act
            var center = new Point(0.5, 0.5);
            var gradient = ThemeGenerator.CreateRadialGradient("TestRadial", center, 0.8, 0.6,
                ("#FF0000", 0.0),
                ("#00FF00", 0.5),
                ("#0000FF", 1.0));

            // Assert
            Assert.Equal("TestRadial", gradient.Name);
            Assert.Equal(GradientType.Radial, gradient.Type);
            Assert.Equal(0.5, gradient.Center.X);
            Assert.Equal(0.5, gradient.Center.Y);
            Assert.Equal(0.8, gradient.RadiusX);
            Assert.Equal(0.6, gradient.RadiusY);
            Assert.Equal(3, gradient.Stops.Count);
        }

        [Fact]
        public void GradientStop_ShouldClampPosition()
        {
            // Arrange & Act
            var stop1 = new Services.GradientStop(Colors.Red, -0.5); // Should clamp to 0
            var stop2 = new Services.GradientStop(Colors.Blue, 1.5);  // Should clamp to 1

            // Assert
            Assert.Equal(0.0, stop1.Position);
            Assert.Equal(1.0, stop2.Position);
        }

        [Fact]
        public async Task ThemeGenerator_CreateSampleGradientTheme_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var themeGenerator = new ThemeGenerator(fileSystemService);

            // Act
            var theme = await themeGenerator.CreateSampleGradientThemeAsync();

            // Assert
            Assert.NotNull(theme);
            Assert.Equal("Ocean Breeze", theme.Name);
            Assert.True(theme.Colors.Count > 0);
            Assert.True(theme.Gradients.Count > 0);
            Assert.Contains("HeaderBackground", theme.Gradients.Keys);
            Assert.Contains("SidebarBackground", theme.Gradients.Keys);
            Assert.Contains("ButtonGradient", theme.Gradients.Keys);
        }

        [Fact]
        public async Task ThemeGenerator_SaveAndLoadThemeObject_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var themeGenerator = new ThemeGenerator(fileSystemService);

            var originalTheme = new Theme
            {
                Name = "TestTheme",
                Description = "Test theme with gradients",
                Colors = new System.Collections.Generic.Dictionary<string, string>
                {
                    { "Primary", "#FF0000" },
                    { "Secondary", "#00FF00" }
                },
                Gradients = new System.Collections.Generic.Dictionary<string, GradientDefinition>
                {
                    {
                        "TestGradient",
                        ThemeGenerator.CreateLinearGradient("TestGradient", 90, 
                            ("#FF0000", 0.0), 
                            ("#0000FF", 1.0))
                    }
                }
            };

            // Act
            await themeGenerator.SaveThemeObjectAsync(originalTheme);
            var loadedTheme = await themeGenerator.LoadThemeObjectAsync("TestTheme");

            // Assert
            Assert.NotNull(loadedTheme);
            Assert.Equal(originalTheme.Name, loadedTheme.Name);
            Assert.Equal(originalTheme.Description, loadedTheme.Description);
            Assert.Equal(originalTheme.Colors.Count, loadedTheme.Colors.Count);
            Assert.Equal(originalTheme.Gradients.Count, loadedTheme.Gradients.Count);
        }

        [Fact]
        public async Task ThemeGenerator_GenerateThemeFromObject_ShouldIncludeGradients()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var themeGenerator = new ThemeGenerator(fileSystemService);

            var theme = new Theme
            {
                Name = "TestTheme",
                Colors = new System.Collections.Generic.Dictionary<string, string>
                {
                    { "Primary", "#007ACC" },
                    { "Secondary", "#6C757D" }
                },
                Gradients = new System.Collections.Generic.Dictionary<string, GradientDefinition>
                {
                    {
                        "HeaderGradient",
                        ThemeGenerator.CreateLinearGradient("HeaderGradient", 45, 
                            ("#007ACC", 0.0), 
                            ("#6C757D", 1.0))
                    }
                }
            };

            // Act
            var themeDict = await themeGenerator.GenerateThemeFromObjectAsync(theme);

            // Assert
            Assert.NotNull(themeDict);
            Assert.Contains("Primary", themeDict.Keys);
            Assert.Contains("Secondary", themeDict.Keys);
            Assert.Contains("Gradient_HeaderGradient", themeDict.Keys);
            
            var gradientValue = themeDict["Gradient_HeaderGradient"].ToString();
            Assert.Contains("linear-gradient", gradientValue);
            Assert.Contains("45deg", gradientValue);
        }

        [Fact]
        public async Task ThemeGenerator_GenerateThemeWithGradients_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var themeGenerator = new ThemeGenerator(fileSystemService);

            var config = new ThemeConfiguration
            {
                Name = "TestGradientConfig",
                PrimaryColor = "#007ACC",
                SecondaryColor = "#6C757D",
                Gradients = new System.Collections.Generic.Dictionary<string, GradientDefinition>
                {
                    {
                        "BackgroundGradient",
                        ThemeGenerator.CreateLinearGradient("BackgroundGradient", 135, 
                            ("#007ACC", 0.0), 
                            ("#6C757D", 1.0))
                    }
                }
            };

            // Act
            var themeDict = await themeGenerator.GenerateThemeAsync(config);

            // Assert
            Assert.NotNull(themeDict);
            Assert.Contains("Primary", themeDict.Keys);
            Assert.Contains("Secondary", themeDict.Keys);
            Assert.Contains("BackgroundGradient", themeDict.Keys);
            
            var gradientValue = themeDict["BackgroundGradient"].ToString();
            Assert.Contains("linear-gradient", gradientValue);
            Assert.Contains("135deg", gradientValue);
        }

        [Fact]
        public void Point_Constructor_ShouldSetValues()
        {
            // Arrange & Act
            var point = new Point(0.3, 0.7);

            // Assert
            Assert.Equal(0.3, point.X);
            Assert.Equal(0.7, point.Y);
        }

        [Fact]
        public void Theme_DefaultValues_ShouldBeSet()
        {
            // Arrange & Act
            var theme = new Theme();

            // Assert
            Assert.Equal(string.Empty, theme.Name);
            Assert.Equal("1.0", theme.Version);
            Assert.NotNull(theme.Colors);
            Assert.NotNull(theme.Gradients);
            Assert.True(theme.CreatedAt <= DateTime.UtcNow);
            Assert.True(theme.UpdatedAt <= DateTime.UtcNow);
        }

        [Fact]
        public async Task ThemeGenerator_LoadNonExistentTheme_ShouldReturnNull()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var themeGenerator = new ThemeGenerator(fileSystemService);

            // Act
            var theme = await themeGenerator.LoadThemeObjectAsync("NonExistentTheme");

            // Assert
            Assert.Null(theme);
        }
    }
}