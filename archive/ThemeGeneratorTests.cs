using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Tests
{
    public class ThemeGeneratorTests : IDisposable
    {
        private readonly string _tempDirectory;
        private readonly MockFileSystemService _mockFileSystemService;
        private readonly ThemeGenerator _themeGenerator;

        public ThemeGeneratorTests()
        {
            _tempDirectory = Path.Combine(Path.GetTempPath(), $"ThemeGeneratorTests_{Guid.NewGuid()}");
            Directory.CreateDirectory(_tempDirectory);
            
            _mockFileSystemService = new MockFileSystemService(_tempDirectory);
            _themeGenerator = new ThemeGenerator(_mockFileSystemService);
        }

        public void Dispose()
        {
            if (Directory.Exists(_tempDirectory))
            {
                Directory.Delete(_tempDirectory, true);
            }
        }

        [Fact]
        public async Task GenerateThemeAsync_WithNullConfig_ShouldThrowArgumentNullException()
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentNullException>(() => _themeGenerator.GenerateThemeAsync(null));
        }

        [Fact]
        public async Task GenerateThemeAsync_WithValidConfig_ShouldGenerateTheme()
        {
            // Arrange
            var config = new ThemeConfiguration
            {
                Name = "TestTheme",
                PrimaryColor = "#007ACC",
                SecondaryColor = "#6C757D",
                BackgroundColor = "#FFFFFF",
                ForegroundColor = "#212529",
                AccentColor = "#FFC107"
            };

            // Act
            var theme = await _themeGenerator.GenerateThemeAsync(config);

            // Assert
            Assert.NotNull(theme);
            Assert.Equal(config.PrimaryColor, theme["Primary"]);
            Assert.Equal(config.SecondaryColor, theme["Secondary"]);
            Assert.Equal(config.BackgroundColor, theme["Background"]);
            Assert.Equal(config.ForegroundColor, theme["Foreground"]);
            Assert.Equal(config.AccentColor, theme["Accent"]);
            
            // Check derived colors exist
            Assert.True(theme.ContainsKey("PrimaryHover"));
            Assert.True(theme.ContainsKey("PrimaryPressed"));
            Assert.True(theme.ContainsKey("SecondaryHover"));
            Assert.True(theme.ContainsKey("BorderColor"));
            Assert.True(theme.ContainsKey("ShadowColor"));
            Assert.True(theme.ContainsKey("TextPrimary"));
            Assert.True(theme.ContainsKey("TextSecondary"));
            Assert.True(theme.ContainsKey("TextDisabled"));
        }

        [Fact]
        public async Task SaveThemeAsync_WithNullThemeName_ShouldThrowArgumentException()
        {
            // Arrange
            var theme = new System.Collections.Generic.Dictionary<string, object>();

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _themeGenerator.SaveThemeAsync(null, theme));
            await Assert.ThrowsAsync<ArgumentException>(() => _themeGenerator.SaveThemeAsync("", theme));
            await Assert.ThrowsAsync<ArgumentException>(() => _themeGenerator.SaveThemeAsync("   ", theme));
        }

        [Fact]
        public async Task SaveThemeAsync_WithNullTheme_ShouldThrowArgumentNullException()
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentNullException>(() => _themeGenerator.SaveThemeAsync("TestTheme", null));
        }

        [Fact]
        public async Task SaveAndLoadTheme_ShouldPersistThemeCorrectly()
        {
            // Arrange
            var config = new ThemeConfiguration
            {
                Name = "PersistenceTestTheme",
                PrimaryColor = "#FF5733",
                BackgroundColor = "#333333"
            };

            // Act - Generate and save theme
            var originalTheme = await _themeGenerator.GenerateThemeAsync(config);
            await _themeGenerator.SaveThemeAsync(config.Name, originalTheme);

            // Act - Load theme
            var loadedTheme = await _themeGenerator.LoadThemeAsync(config.Name);

            // Assert
            Assert.NotNull(loadedTheme);
            Assert.Equal(originalTheme.Count, loadedTheme.Count);
        }

        [Fact]
        public async Task LoadThemeAsync_WithNonExistentTheme_ShouldReturnNull()
        {
            // Act
            var theme = await _themeGenerator.LoadThemeAsync("NonExistentTheme");

            // Assert
            Assert.Null(theme);
        }

        [Fact]
        public async Task LoadThemeAsync_WithNullOrEmptyName_ShouldReturnNull()
        {
            // Act & Assert
            Assert.Null(await _themeGenerator.LoadThemeAsync(null));
            Assert.Null(await _themeGenerator.LoadThemeAsync(""));
            Assert.Null(await _themeGenerator.LoadThemeAsync("   "));
        }

        [Fact]
        public void GetAvailableThemes_WithNoThemes_ShouldReturnEmptyArray()
        {
            // Act
            var themes = _themeGenerator.GetAvailableThemes();

            // Assert
            Assert.NotNull(themes);
            Assert.Empty(themes);
        }

        [Fact]
        public async Task GetAvailableThemes_WithSavedThemes_ShouldReturnThemeNames()
        {
            // Arrange
            var config1 = new ThemeConfiguration { Name = "Theme1" };
            var config2 = new ThemeConfiguration { Name = "Theme2" };
            
            var theme1 = await _themeGenerator.GenerateThemeAsync(config1);
            var theme2 = await _themeGenerator.GenerateThemeAsync(config2);

            // Act
            var themes = _themeGenerator.GetAvailableThemes();

            // Assert
            Assert.NotNull(themes);
            Assert.Equal(2, themes.Length);
            Assert.Contains("Theme1", themes);
            Assert.Contains("Theme2", themes);
        }

        // Mock FileSystemService for testing
        private class MockFileSystemService : IFileSystemService
        {
            private readonly string _basePath;

            public MockFileSystemService(string basePath)
            {
                _basePath = basePath;
            }

            public string GetAppDataPath() => _basePath;
            public string GetDocumentsPath() => Path.Combine(_basePath, "Documents");
            public bool FileExists(string path) => File.Exists(path);
            public bool DirectoryExists(string path) => Directory.Exists(path);
            public void CreateDirectory(string path) => Directory.CreateDirectory(path);
            public Task<string> ReadAllTextAsync(string path) => File.ReadAllTextAsync(path);
            public Task WriteAllTextAsync(string path, string content) => File.WriteAllTextAsync(path, content);
            public void DeleteFile(string path) => File.Delete(path);
            public void DeleteDirectory(string path, bool recursive = true) => Directory.Delete(path, recursive);
            public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false)
                => Directory.GetFiles(path, searchPattern, recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
            public string[] GetDirectories(string path) => Directory.GetDirectories(path);
            public long GetFileSize(string path) => new FileInfo(path).Length;
            public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false) 
                => File.Copy(sourcePath, destinationPath, overwrite);
            public void MoveFile(string sourcePath, string destinationPath) => File.Move(sourcePath, destinationPath);
            public string GetTailorPacksPath() => Path.Combine(_basePath, "TailorPacks");
            public string GetSettingsPath() => Path.Combine(_basePath, "settings.json");
            public string GetLogsPath() => Path.Combine(_basePath, "Logs");
        }
    }
}