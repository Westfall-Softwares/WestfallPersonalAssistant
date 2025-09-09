using System;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using WestfallPersonalAssistant.Platform;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Cross-platform notification service with null guards for headless environments
    /// </summary>
    public class NotificationService
    {
        private readonly IPlatformNotificationManager _platformNotificationManager;
        private readonly IPlatformService _platformService;

        public NotificationService(IPlatformNotificationManager platformNotificationManager, IPlatformService platformService)
        {
            _platformNotificationManager = platformNotificationManager ?? throw new ArgumentNullException(nameof(platformNotificationManager));
            _platformService = platformService ?? throw new ArgumentNullException(nameof(platformService));
        }

        /// <summary>
        /// Show a toast notification with null guards for headless Linux environments
        /// </summary>
        /// <param name="title">Notification title</param>
        /// <param name="message">Notification message</param>
        /// <returns>True if notification was shown successfully</returns>
        public async Task<bool> ShowToastAsync(string title, string message)
        {
            try
            {
                // Check if platform supports notifications
                if (!_platformNotificationManager.IsSupported)
                {
                    Console.WriteLine($"[INFO] Toast notifications not supported on this platform. Title: {title}, Message: {message}");
                    return false;
                }

                // Create toast notification
                var toast = _platformNotificationManager.CreateToast(title, message);
                
                // Null guard: If CreateToast() returns null, log info and return without throwing
                if (toast == null)
                {
                    Console.WriteLine($"[INFO] CreateToast returned null (likely headless environment). Title: {title}, Message: {message}");
                    return false;
                }

                // Show the toast notification
                var success = _platformNotificationManager.ShowToast(toast);
                
                if (success)
                {
                    Console.WriteLine($"[INFO] Toast notification shown successfully: {title}");
                }
                else
                {
                    Console.WriteLine($"[WARN] Failed to show toast notification: {title}");
                }

                return success;
            }
            catch (Exception ex)
            {
                // Log the error but don't throw - this prevents crashes in headless environments
                Console.WriteLine($"[ERROR] Error showing toast notification: {ex.Message}. Title: {title}, Message: {message}");
                return false;
            }
        }

        /// <summary>
        /// Show a simple notification using platform service as fallback
        /// </summary>
        /// <param name="title">Notification title</param>
        /// <param name="message">Notification message</param>
        /// <returns>True if notification was shown successfully</returns>
        public async Task<bool> ShowNotificationAsync(string title, string message)
        {
            try
            {
                // First try toast notification
                var toastSuccess = await ShowToastAsync(title, message);
                if (toastSuccess)
                {
                    return true;
                }

                // Fallback to platform service notification
                _platformService.ShowNotification(title, message);
                Console.WriteLine($"[INFO] Fallback notification shown: {title}");
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] Error showing notification: {ex.Message}. Title: {title}, Message: {message}");
                return false;
            }
        }

        /// <summary>
        /// Check if the current environment supports toast notifications
        /// </summary>
        /// <returns>True if toast notifications are supported</returns>
        public bool IsToastSupported()
        {
            try
            {
                return _platformNotificationManager.IsSupported;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[WARN] Error checking toast support: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Check if running in a headless environment
        /// </summary>
        /// <returns>True if likely running headless</returns>
        public bool IsHeadlessEnvironment()
        {
            try
            {
                // Check for common headless indicators
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    // Check if DISPLAY environment variable is set
                    var display = Environment.GetEnvironmentVariable("DISPLAY");
                    if (string.IsNullOrEmpty(display))
                    {
                        Console.WriteLine("[INFO] Detected headless Linux environment (no DISPLAY)");
                        return true;
                    }

                    // Check if running in Docker/container
                    var dockerEnv = Environment.GetEnvironmentVariable("DOCKER_CONTAINER");
                    if (!string.IsNullOrEmpty(dockerEnv))
                    {
                        Console.WriteLine("[INFO] Detected Docker container environment");
                        return true;
                    }

                    // Check if running in SSH session without X11 forwarding
                    var sshConnection = Environment.GetEnvironmentVariable("SSH_CONNECTION");
                    if (!string.IsNullOrEmpty(sshConnection) && string.IsNullOrEmpty(display))
                    {
                        Console.WriteLine("[INFO] Detected SSH session without X11 forwarding");
                        return true;
                    }
                }

                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[WARN] Error checking headless environment: {ex.Message}");
                return false;
            }
        }
    }
}