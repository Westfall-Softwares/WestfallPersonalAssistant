using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Platform
{
    /// <summary>
    /// Linux implementation of platform notification manager
    /// </summary>
    public class LinuxPlatformNotificationManager : IPlatformNotificationManager
    {
        public bool IsSupported => CheckNotificationSupport();

        public object? CreateToast(string title, string message)
        {
            try
            {
                // Check if we're in a headless environment
                if (IsHeadlessEnvironment())
                {
                    // Return null for headless environments - this is expected behavior
                    return null;
                }

                // Check if notify-send is available
                if (!IsNotifySendAvailable())
                {
                    return null;
                }

                // Create a simple toast object with the notification data
                return new LinuxToast
                {
                    Title = title ?? string.Empty,
                    Message = message ?? string.Empty,
                    Timeout = 5000 // 5 seconds default
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] CreateToast failed on Linux: {ex.Message}");
                return null;
            }
        }

        public bool ShowToast(object toast)
        {
            try
            {
                if (toast is not LinuxToast linuxToast)
                {
                    return false;
                }

                // Use notify-send to show the notification
                var processInfo = new ProcessStartInfo
                {
                    FileName = "notify-send",
                    Arguments = $"-t {linuxToast.Timeout} \"{EscapeShellArgument(linuxToast.Title)}\" \"{EscapeShellArgument(linuxToast.Message)}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardError = true,
                    RedirectStandardOutput = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    process.WaitForExit(2000); // Wait max 2 seconds
                    return process.ExitCode == 0;
                }

                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] ShowToast failed on Linux: {ex.Message}");
                return false;
            }
        }

        private bool CheckNotificationSupport()
        {
            try
            {
                // In headless environments, notifications are not supported
                if (IsHeadlessEnvironment())
                {
                    return false;
                }

                // Check if notify-send is available
                return IsNotifySendAvailable();
            }
            catch
            {
                return false;
            }
        }

        private bool IsHeadlessEnvironment()
        {
            try
            {
                // Check if DISPLAY environment variable is set
                var display = Environment.GetEnvironmentVariable("DISPLAY");
                if (string.IsNullOrEmpty(display))
                {
                    return true;
                }

                // Check if running in container
                var dockerEnv = Environment.GetEnvironmentVariable("DOCKER_CONTAINER");
                if (!string.IsNullOrEmpty(dockerEnv))
                {
                    return true;
                }

                // Check if running in SSH without X11 forwarding
                var sshConnection = Environment.GetEnvironmentVariable("SSH_CONNECTION");
                if (!string.IsNullOrEmpty(sshConnection) && string.IsNullOrEmpty(display))
                {
                    return true;
                }

                return false;
            }
            catch
            {
                return true; // Assume headless if we can't determine
            }
        }

        private bool IsNotifySendAvailable()
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = "which",
                    Arguments = "notify-send",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    process.WaitForExit(1000);
                    return process.ExitCode == 0;
                }

                return false;
            }
            catch
            {
                return false;
            }
        }

        private string EscapeShellArgument(string argument)
        {
            if (string.IsNullOrEmpty(argument))
            {
                return string.Empty;
            }

            // Escape special characters for shell
            return argument.Replace("\"", "\\\"")
                          .Replace("\\", "\\\\")
                          .Replace("`", "\\`")
                          .Replace("$", "\\$");
        }

        private class LinuxToast
        {
            public string Title { get; set; } = string.Empty;
            public string Message { get; set; } = string.Empty;
            public int Timeout { get; set; } = 5000;
        }
    }
}