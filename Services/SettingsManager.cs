using System;
using System.Text.Json;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public class SettingsManager : ISettingsManager
    {
        private readonly IFileSystemService _fileSystemService;
        private ApplicationSettings _currentSettings;
        
        public event EventHandler<ApplicationSettings>? SettingsChanged;
        
        public SettingsManager(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService;
            _currentSettings = new ApplicationSettings();
        }
        
        public async Task<ApplicationSettings> LoadSettingsAsync()
        {
            try
            {
                var settingsPath = _fileSystemService.GetSettingsPath();
                
                if (!_fileSystemService.FileExists(settingsPath))
                {
                    // Create default settings file
                    _currentSettings = new ApplicationSettings();
                    await SaveSettingsAsync(_currentSettings);
                    return _currentSettings;
                }
                
                var jsonContent = await _fileSystemService.ReadAllTextAsync(settingsPath);
                
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true,
                    WriteIndented = true
                };
                
                var settings = JsonSerializer.Deserialize<ApplicationSettings>(jsonContent, options);
                _currentSettings = settings ?? new ApplicationSettings();
                
                return _currentSettings;
            }
            catch (Exception ex)
            {
                // Log error and return default settings
                Console.WriteLine($"Error loading settings: {ex.Message}");
                _currentSettings = new ApplicationSettings();
                return _currentSettings;
            }
        }
        
        public async Task SaveSettingsAsync(ApplicationSettings settings)
        {
            try
            {
                var settingsPath = _fileSystemService.GetSettingsPath();
                
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true,
                    WriteIndented = true
                };
                
                var jsonContent = JsonSerializer.Serialize(settings, options);
                await _fileSystemService.WriteAllTextAsync(settingsPath, jsonContent);
                
                _currentSettings = settings;
                SettingsChanged?.Invoke(this, _currentSettings);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving settings: {ex.Message}");
                throw;
            }
        }
        
        public ApplicationSettings GetCurrentSettings()
        {
            return _currentSettings;
        }
        
        public async Task UpdateSettingAsync<T>(string key, T value)
        {
            try
            {
                // Use reflection to update the specific property
                var property = typeof(ApplicationSettings).GetProperty(key);
                if (property != null && property.CanWrite)
                {
                    property.SetValue(_currentSettings, value);
                    await SaveSettingsAsync(_currentSettings);
                }
                else
                {
                    throw new ArgumentException($"Property '{key}' not found or is read-only");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error updating setting '{key}': {ex.Message}");
                throw;
            }
        }
        
        public async Task ResetSettingsAsync()
        {
            var defaultSettings = new ApplicationSettings();
            await SaveSettingsAsync(defaultSettings);
        }
        
        public bool SettingsExist()
        {
            var settingsPath = _fileSystemService.GetSettingsPath();
            return _fileSystemService.FileExists(settingsPath);
        }
        
        /// <summary>
        /// Migrate settings from older versions if needed
        /// </summary>
        public async Task MigrateSettingsAsync()
        {
            if (!SettingsExist())
                return;
                
            var settings = await LoadSettingsAsync();
            
            // Check if migration is needed based on version
            if (string.IsNullOrEmpty(settings.Version) || settings.Version != "1.0.0")
            {
                // Perform migration logic here
                settings.Version = "1.0.0";
                await SaveSettingsAsync(settings);
            }
        }
    }
}