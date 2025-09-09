using System;
using System.Diagnostics;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Platform
{
    /// <summary>
    /// macOS implementation of platform notification manager
    /// </summary>
    public class MacOSPlatformNotificationManager : IPlatformNotificationManager
    {
        public bool IsSupported => IsOsaScriptAvailable();

        public object? CreateToast(string title, string message)
        {
            try
            {
                if (!IsOsaScriptAvailable())
                {
                    return null;
                }

                return new MacOSToast
                {
                    Title = title ?? string.Empty,
                    Message = message ?? string.Empty
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] CreateToast failed on macOS: {ex.Message}");
                return null;
            }
        }

        public bool ShowToast(object toast)
        {
            try
            {
                if (toast is not MacOSToast macToast)
                {
                    return false;
                }

                var script = $"display notification \"{EscapeAppleScript(macToast.Message)}\" with title \"{EscapeAppleScript(macToast.Title)}\"";
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = "osascript",
                    Arguments = $"-e \"{script}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardError = true,
                    RedirectStandardOutput = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    process.WaitForExit(5000); // Wait max 5 seconds
                    return process.ExitCode == 0;
                }

                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] ShowToast failed on macOS: {ex.Message}");
                return false;
            }
        }

        private bool IsOsaScriptAvailable()
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = "which",
                    Arguments = "osascript",
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

        private string EscapeAppleScript(string input)
        {
            if (string.IsNullOrEmpty(input))
            {
                return string.Empty;
            }

            return input.Replace("\\", "\\\\")
                        .Replace("\"", "\\\"");
        }

        private class MacOSToast
        {
            public string Title { get; set; } = string.Empty;
            public string Message { get; set; } = string.Empty;
        }
    }
}