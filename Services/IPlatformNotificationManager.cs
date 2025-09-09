using System;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for platform-specific notification management
    /// </summary>
    public interface IPlatformNotificationManager
    {
        /// <summary>
        /// Create a toast notification
        /// </summary>
        /// <param name="title">Notification title</param>
        /// <param name="message">Notification message</param>
        /// <returns>Toast notification object, or null if not supported</returns>
        object? CreateToast(string title, string message);

        /// <summary>
        /// Show a toast notification
        /// </summary>
        /// <param name="toast">Toast object created by CreateToast</param>
        /// <returns>True if notification was shown successfully</returns>
        bool ShowToast(object toast);

        /// <summary>
        /// Check if toast notifications are supported on this platform
        /// </summary>
        bool IsSupported { get; }
    }
}