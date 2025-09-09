using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Threading;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Implementation of security logging with encrypted storage and log rotation
    /// </summary>
    public class SecurityLogger : ISecurityLogger, IDisposable
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly ISecureStorageService _secureStorageService;
        private readonly string _logsDirectory;
        private readonly string _currentLogFile;
        private readonly Timer _rotationTimer;
        private readonly SemaphoreSlim _logSemaphore = new(1, 1);
        
        private SecurityLogLevel _logLevel = SecurityLogLevel.Info;
        private bool _auditLoggingEnabled = true;
        private readonly int _maxLogFileSize = 10 * 1024 * 1024; // 10MB
        private readonly int _maxLogFiles = 10;
        private bool _disposed = false;
        
        public SecurityLogger(IFileSystemService fileSystemService, ISecureStorageService secureStorageService)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _secureStorageService = secureStorageService ?? throw new ArgumentNullException(nameof(secureStorageService));
            
            _logsDirectory = Path.Combine(_fileSystemService.GetLogsPath(), "security");
            _currentLogFile = Path.Combine(_logsDirectory, $"security_{DateTime.UtcNow:yyyyMMdd}.log");
            
            EnsureLogsDirectory();
            
            // Set up daily log rotation timer
            var rotationTime = DateTime.Today.AddDays(1).AddHours(1); // 1 AM next day
            var dueTime = rotationTime - DateTime.Now;
            _rotationTimer = new Timer(async _ => await RotateLogsAsync(), null, dueTime, TimeSpan.FromDays(1));
        }
        
        private void EnsureLogsDirectory()
        {
            if (!_fileSystemService.DirectoryExists(_logsDirectory))
            {
                _fileSystemService.CreateDirectory(_logsDirectory);
            }
        }
        
        public async Task LogSecurityEventAsync(SecurityEvent securityEvent)
        {
            if (!_auditLoggingEnabled || securityEvent.LogLevel < _logLevel)
                return;
                
            await _logSemaphore.WaitAsync();
            try
            {
                await WriteLogEntryAsync(securityEvent);
                
                // Check if log rotation is needed
                if (_fileSystemService.FileExists(_currentLogFile) && 
                    _fileSystemService.GetFileSize(_currentLogFile) > _maxLogFileSize)
                {
                    await RotateLogsAsync();
                }
            }
            finally
            {
                _logSemaphore.Release();
            }
        }
        
        public async Task LogAuthenticationAttemptAsync(string username, bool success, string? failureReason = null)
        {
            var securityEvent = new SecurityEvent
            {
                EventType = SecurityEventType.Authentication,
                LogLevel = success ? SecurityLogLevel.Info : SecurityLogLevel.Warning,
                User = SanitizeUsername(username),
                Action = success ? "Login Success" : "Login Failed",
                Resource = "Authentication System",
                Success = success,
                FailureReason = SanitizeFailureReason(failureReason)
            };
            
            await LogSecurityEventAsync(securityEvent);
        }
        
        public async Task LogPrivilegedOperationAsync(string operation, string user, Dictionary<string, object>? parameters = null)
        {
            var securityEvent = new SecurityEvent
            {
                EventType = SecurityEventType.PrivilegedOperation,
                LogLevel = SecurityLogLevel.Info,
                User = SanitizeUsername(user),
                Action = SanitizeOperation(operation),
                Resource = "Privileged Operation",
                Success = true,
                Metadata = SanitizeMetadata(parameters ?? new Dictionary<string, object>())
            };
            
            await LogSecurityEventAsync(securityEvent);
        }
        
        public async Task LogDataAccessAsync(string resourceType, string resourceId, string action, string user)
        {
            var securityEvent = new SecurityEvent
            {
                EventType = SecurityEventType.DataAccess,
                LogLevel = SecurityLogLevel.Info,
                User = user,
                Action = action,
                Resource = $"{resourceType}:{resourceId}",
                Success = true
            };
            
            await LogSecurityEventAsync(securityEvent);
        }
        
        public async Task LogFileOperationAsync(string filePath, string operation, string user, bool success)
        {
            var securityEvent = new SecurityEvent
            {
                EventType = SecurityEventType.FileOperation,
                LogLevel = success ? SecurityLogLevel.Info : SecurityLogLevel.Warning,
                User = user,
                Action = operation,
                Resource = filePath,
                Success = success
            };
            
            await LogSecurityEventAsync(securityEvent);
        }
        
        public async Task<List<SecurityEvent>> GetSecurityEventsAsync(DateTime? fromDate = null, DateTime? toDate = null, SecurityEventType? eventType = null)
        {
            var events = new List<SecurityEvent>();
            var logFiles = GetLogFiles(fromDate, toDate);
            
            foreach (var logFile in logFiles)
            {
                var fileEvents = await ReadLogFileAsync(logFile);
                events.AddRange(fileEvents);
            }
            
            if (eventType.HasValue)
            {
                events = events.Where(e => eventType.Value == e.EventType).ToList();
            }
            
            return events.OrderByDescending(e => e.Timestamp).ToList();
        }
        
        public async Task<List<SecurityEvent>> GetFailedLoginsAsync(TimeSpan timeRange)
        {
            var fromDate = DateTime.UtcNow - timeRange;
            var events = await GetSecurityEventsAsync(fromDate, DateTime.UtcNow, SecurityEventType.Authentication);
            return events.Where(e => !e.Success).ToList();
        }
        
        public async Task<List<SecurityEvent>> GetPrivilegedOperationsAsync(string? user = null, TimeSpan? timeRange = null)
        {
            var fromDate = timeRange.HasValue ? DateTime.UtcNow - timeRange.Value : (DateTime?)null;
            var events = await GetSecurityEventsAsync(fromDate, DateTime.UtcNow, SecurityEventType.PrivilegedOperation);
            
            if (!string.IsNullOrEmpty(user))
            {
                events = events.Where(e => e.User.Equals(user, StringComparison.OrdinalIgnoreCase)).ToList();
            }
            
            return events;
        }
        
        public async Task<bool> CheckSuspiciousActivityAsync(string user, TimeSpan timeRange)
        {
            var failedLogins = await GetFailedLoginCountAsync(user, timeRange);
            var privilegedOps = await GetPrivilegedOperationsAsync(user, timeRange);
            
            // Define suspicious activity thresholds
            const int maxFailedLogins = 5;
            const int maxPrivilegedOpsPerHour = 20;
            
            var privilegedOpsCount = privilegedOps.Count;
            var privilegedOpsPerHour = timeRange.TotalHours > 0 ? privilegedOpsCount / timeRange.TotalHours : privilegedOpsCount;
            
            return failedLogins >= maxFailedLogins || privilegedOpsPerHour >= maxPrivilegedOpsPerHour;
        }
        
        public async Task<int> GetFailedLoginCountAsync(string user, TimeSpan timeRange)
        {
            var failedLogins = await GetFailedLoginsAsync(timeRange);
            return failedLogins.Count(e => e.User.Equals(user, StringComparison.OrdinalIgnoreCase));
        }
        
        public async Task RotateLogsAsync()
        {
            await _logSemaphore.WaitAsync();
            try
            {
                // Get all existing log files
                var logFiles = _fileSystemService.GetFiles(_logsDirectory, "security_*.log")
                    .OrderByDescending(f => f)
                    .ToArray();
                
                // Delete excess log files
                for (int i = _maxLogFiles; i < logFiles.Length; i++)
                {
                    _fileSystemService.DeleteFile(logFiles[i]);
                }
                
                // Archive current log if it exists and has content
                if (_fileSystemService.FileExists(_currentLogFile) && _fileSystemService.GetFileSize(_currentLogFile) > 0)
                {
                    var archiveName = Path.Combine(_logsDirectory, $"security_{DateTime.UtcNow:yyyyMMdd_HHmmss}.log");
                    _fileSystemService.MoveFile(_currentLogFile, archiveName);
                }
            }
            finally
            {
                _logSemaphore.Release();
            }
        }
        
        public Task PurgeOldLogsAsync(TimeSpan retentionPeriod)
        {
            var cutoffDate = DateTime.UtcNow - retentionPeriod;
            var logFiles = _fileSystemService.GetFiles(_logsDirectory, "security_*.log");
            
            foreach (var logFile in logFiles)
            {
                var fileDate = ExtractDateFromLogFileName(logFile);
                if (fileDate.HasValue && fileDate.Value < cutoffDate)
                {
                    _fileSystemService.DeleteFile(logFile);
                }
            }
            
            return Task.CompletedTask;
        }
        
        public void SetLogLevel(SecurityLogLevel level)
        {
            _logLevel = level;
        }
        
        public void EnableAuditLogging(bool enabled)
        {
            _auditLoggingEnabled = enabled;
        }
        
        private async Task WriteLogEntryAsync(SecurityEvent securityEvent)
        {
            try
            {
                var logEntry = JsonSerializer.Serialize(securityEvent, new JsonSerializerOptions
                {
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                    WriteIndented = false
                });
                
                var logLine = $"{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss.fff} UTC | {logEntry}\n";
                
                // Encrypt the log entry before writing
                var encryptedLogLine = _secureStorageService.EncryptString(logLine);
                
                await File.AppendAllTextAsync(_currentLogFile, encryptedLogLine + "\n");
            }
            catch (Exception ex)
            {
                // Fallback to plain text logging if encryption fails
                var fallbackLog = $"{DateTime.UtcNow:yyyy-MM-dd HH:mm:ss.fff} UTC | ERROR | Failed to encrypt log: {ex.Message}\n";
                await File.AppendAllTextAsync(_currentLogFile, fallbackLog);
            }
        }
        
        private async Task<List<SecurityEvent>> ReadLogFileAsync(string logFile)
        {
            var events = new List<SecurityEvent>();
            
            try
            {
                var lines = await File.ReadAllLinesAsync(logFile);
                
                foreach (var line in lines)
                {
                    if (string.IsNullOrWhiteSpace(line))
                        continue;
                        
                    try
                    {
                        // Try to decrypt the line first
                        var decryptedLine = _secureStorageService.DecryptString(line);
                        
                        // Extract JSON part (after the timestamp)
                        var jsonStart = decryptedLine.IndexOf(" | ") + 3;
                        if (jsonStart > 2)
                        {
                            var json = decryptedLine.Substring(jsonStart);
                            var securityEvent = JsonSerializer.Deserialize<SecurityEvent>(json, new JsonSerializerOptions
                            {
                                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                            });
                            
                            if (securityEvent != null)
                            {
                                events.Add(securityEvent);
                            }
                        }
                    }
                    catch
                    {
                        // Skip corrupted or unreadable entries
                        continue;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading log file {logFile}: {ex.Message}");
            }
            
            return events;
        }
        
        private string[] GetLogFiles(DateTime? fromDate, DateTime? toDate)
        {
            var allLogFiles = _fileSystemService.GetFiles(_logsDirectory, "security_*.log");
            
            if (!fromDate.HasValue && !toDate.HasValue)
                return allLogFiles;
            
            return allLogFiles.Where(file =>
            {
                var fileDate = ExtractDateFromLogFileName(file);
                if (!fileDate.HasValue)
                    return false;
                    
                if (fromDate.HasValue && fileDate.Value.Date < fromDate.Value.Date)
                    return false;
                    
                if (toDate.HasValue && fileDate.Value.Date > toDate.Value.Date)
                    return false;
                    
                return true;
            }).ToArray();
        }
        
        private DateTime? ExtractDateFromLogFileName(string fileName)
        {
            try
            {
                var name = Path.GetFileNameWithoutExtension(fileName);
                var parts = name.Split('_');
                
                if (parts.Length >= 2 && DateTime.TryParseExact(parts[1], "yyyyMMdd", null, System.Globalization.DateTimeStyles.None, out var date))
                {
                    return date;
                }
                
                if (parts.Length >= 3 && DateTime.TryParseExact($"{parts[1]}_{parts[2]}", "yyyyMMdd_HHmmss", null, System.Globalization.DateTimeStyles.None, out var dateTime))
                {
                    return dateTime;
                }
            }
            catch
            {
                // Ignore parsing errors
            }
            
            return null;
        }
        
        /// <summary>
        /// Sanitizes sensitive data from security logs
        /// </summary>
        private string SanitizeUsername(string username)
        {
            if (string.IsNullOrEmpty(username))
                return "[Empty]";
                
            // Don't log full usernames - use first character + length
            if (username.Length <= 2)
                return "[Short]";
                
            return $"{username[0]}***({username.Length})";
        }
        
        private string? SanitizeFailureReason(string? failureReason)
        {
            if (string.IsNullOrEmpty(failureReason))
                return null;
                
            // Remove potentially sensitive information from failure reasons
            var sanitized = failureReason;
            
            // Remove file paths
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"[A-Za-z]:\\[^\s]+", "[FILE_PATH]");
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"/[^\s]+", "[FILE_PATH]");
            
            // Remove potential passwords or keys
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"(?i)(password|key|token|secret)[=:\s]+[^\s]+", "$1=[REDACTED]");
            
            return sanitized;
        }
        
        private string SanitizeOperation(string operation)
        {
            if (string.IsNullOrEmpty(operation))
                return "[Unknown]";
                
            // Remove file paths from operation descriptions
            var sanitized = operation;
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"[A-Za-z]:\\[^\s]+", "[FILE_PATH]");
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"/[^\s]+", "[FILE_PATH]");
            
            return sanitized;
        }
        
        private Dictionary<string, object> SanitizeMetadata(Dictionary<string, object> metadata)
        {
            var sanitized = new Dictionary<string, object>();
            
            foreach (var kvp in metadata)
            {
                var key = kvp.Key?.ToLowerInvariant();
                var value = kvp.Value;
                
                // Skip sensitive keys entirely
                if (key != null && (key.Contains("password") || key.Contains("key") || 
                                   key.Contains("token") || key.Contains("secret") ||
                                   key.Contains("credential")))
                {
                    sanitized[kvp.Key] = "[REDACTED]";
                    continue;
                }
                
                // Sanitize string values
                if (value is string stringValue)
                {
                    var sanitizedValue = stringValue;
                    
                    // Remove file paths
                    sanitizedValue = System.Text.RegularExpressions.Regex.Replace(sanitizedValue, @"[A-Za-z]:\\[^\s]+", "[FILE_PATH]");
                    sanitizedValue = System.Text.RegularExpressions.Regex.Replace(sanitizedValue, @"/[^\s]+", "[FILE_PATH]");
                    
                    sanitized[kvp.Key] = sanitizedValue;
                }
                else
                {
                    sanitized[kvp.Key] = value;
                }
            }
            
            return sanitized;
        }
        
        public void Dispose()
        {
            if (!_disposed)
            {
                _rotationTimer?.Dispose();
                _logSemaphore?.Dispose();
                _disposed = true;
            }
        }
    }
}