using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for secure logging and audit trail management
    /// </summary>
    public interface ISecurityLogger
    {
        // Audit logging methods
        Task LogSecurityEventAsync(SecurityEvent securityEvent);
        Task LogAuthenticationAttemptAsync(string username, bool success, string? failureReason = null);
        Task LogPrivilegedOperationAsync(string operation, string user, Dictionary<string, object>? parameters = null);
        Task LogDataAccessAsync(string resourceType, string resourceId, string action, string user);
        Task LogFileOperationAsync(string filePath, string operation, string user, bool success);
        
        // Query methods
        Task<List<SecurityEvent>> GetSecurityEventsAsync(DateTime? fromDate = null, DateTime? toDate = null, SecurityEventType? eventType = null);
        Task<List<SecurityEvent>> GetFailedLoginsAsync(TimeSpan timeRange);
        Task<List<SecurityEvent>> GetPrivilegedOperationsAsync(string? user = null, TimeSpan? timeRange = null);
        
        // Security monitoring
        Task<bool> CheckSuspiciousActivityAsync(string user, TimeSpan timeRange);
        Task<int> GetFailedLoginCountAsync(string user, TimeSpan timeRange);
        
        // Log management
        Task RotateLogsAsync();
        Task PurgeOldLogsAsync(TimeSpan retentionPeriod);
        
        // Settings
        void SetLogLevel(SecurityLogLevel level);
        void EnableAuditLogging(bool enabled);
    }
    
    public enum SecurityEventType
    {
        Authentication,
        Authorization,
        DataAccess,
        FileOperation,
        PrivilegedOperation,
        SecurityViolation,
        ConfigurationChange,
        SystemEvent
    }
    
    public enum SecurityLogLevel
    {
        Info,
        Warning,
        Error,
        Critical
    }
    
    public class SecurityEvent
    {
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
        public SecurityEventType EventType { get; set; }
        public SecurityLogLevel LogLevel { get; set; }
        public string User { get; set; } = string.Empty;
        public string Action { get; set; } = string.Empty;
        public string Resource { get; set; } = string.Empty;
        public bool Success { get; set; }
        public string? FailureReason { get; set; }
        public Dictionary<string, object> Metadata { get; set; } = new();
        public string IpAddress { get; set; } = string.Empty;
        public string UserAgent { get; set; } = string.Empty;
        public string SessionId { get; set; } = string.Empty;
    }
}