using System;
using System.Diagnostics;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Platform
{
    /// <summary>
    /// Windows implementation of platform notification manager
    /// </summary>
    public class WindowsPlatformNotificationManager : IPlatformNotificationManager
    {
        public bool IsSupported => true; // Windows generally supports notifications

        public object? CreateToast(string title, string message)
        {
            try
            {
                return new WindowsToast
                {
                    Title = title ?? string.Empty,
                    Message = message ?? string.Empty,
                    Duration = 5 // 5 seconds default
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] CreateToast failed on Windows: {ex.Message}");
                return null;
            }
        }

        public bool ShowToast(object toast)
        {
            try
            {
                if (toast is not WindowsToast windowsToast)
                {
                    return false;
                }

                // Try to use PowerShell for Windows 10 toast notifications
                return ShowPowerShellToast(windowsToast);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] ShowToast failed on Windows: {ex.Message}");
                return false;
            }
        }

        private bool ShowPowerShellToast(WindowsToast toast)
        {
            try
            {
                var script = $@"
                Add-Type -AssemblyName System.Windows.Forms
                $notify = New-Object System.Windows.Forms.NotifyIcon
                $notify.Icon = [System.Drawing.SystemIcons]::Information
                $notify.Visible = $true
                $notify.ShowBalloonTip({toast.Duration * 1000}, ""{EscapePowerShellString(toast.Title)}"", ""{EscapePowerShellString(toast.Message)}"", [System.Windows.Forms.ToolTipIcon]::Info)
                Start-Sleep -Seconds {toast.Duration}
                $notify.Dispose()
                ";

                var processInfo = new ProcessStartInfo
                {
                    FileName = "powershell",
                    Arguments = $"-Command \"{script}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardError = true,
                    RedirectStandardOutput = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    process.WaitForExit(10000); // Wait max 10 seconds
                    return process.ExitCode == 0;
                }

                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] PowerShell toast failed: {ex.Message}");
                return false;
            }
        }

        private string EscapePowerShellString(string input)
        {
            if (string.IsNullOrEmpty(input))
            {
                return string.Empty;
            }

            return input.Replace("\"", "\"\"")
                        .Replace("'", "''")
                        .Replace("`", "``");
        }

        private class WindowsToast
        {
            public string Title { get; set; } = string.Empty;
            public string Message { get; set; } = string.Empty;
            public int Duration { get; set; } = 5;
        }
    }
}