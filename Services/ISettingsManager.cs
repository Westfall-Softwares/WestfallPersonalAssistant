using System;
using System.Text.Json;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Models;

namespace WestfallPersonalAssistant.Services
{
    public interface ISettingsManager
    {
        /// <summary>
        /// Load application settings
        /// </summary>
        Task<ApplicationSettings> LoadSettingsAsync();
        
        /// <summary>
        /// Save application settings
        /// </summary>
        Task SaveSettingsAsync(ApplicationSettings settings);
        
        /// <summary>
        /// Get current application settings
        /// </summary>
        ApplicationSettings GetCurrentSettings();
        
        /// <summary>
        /// Update a specific setting
        /// </summary>
        Task UpdateSettingAsync<T>(string key, T value);
        
        /// <summary>
        /// Reset settings to default values
        /// </summary>
        Task ResetSettingsAsync();
        
        /// <summary>
        /// Check if settings file exists
        /// </summary>
        bool SettingsExist();
        
        /// <summary>
        /// Event fired when settings are changed
        /// </summary>
        event EventHandler<ApplicationSettings>? SettingsChanged;
    }
}