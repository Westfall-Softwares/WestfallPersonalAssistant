using System;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    public interface IDatabaseService
    {
        /// <summary>
        /// Initialize the database and create tables if they don't exist
        /// </summary>
        Task InitializeAsync();
        
        /// <summary>
        /// Execute a non-query SQL command
        /// </summary>
        Task<int> ExecuteNonQueryAsync(string sql, params object[] parameters);
        
        /// <summary>
        /// Execute a scalar SQL command
        /// </summary>
        Task<T?> ExecuteScalarAsync<T>(string sql, params object[] parameters) where T : struct;
        
        /// <summary>
        /// Execute a query and return results
        /// </summary>
        Task<T[]> QueryAsync<T>(string sql, Func<object[], T> mapper, params object[] parameters);
        
        /// <summary>
        /// Check if the database file exists
        /// </summary>
        bool DatabaseExists();
        
        /// <summary>
        /// Create a backup of the database
        /// </summary>
        Task<bool> BackupDatabaseAsync(string backupPath);
        
        /// <summary>
        /// Restore database from backup
        /// </summary>
        Task<bool> RestoreDatabaseAsync(string backupPath);
        
        /// <summary>
        /// Get database file size
        /// </summary>
        long GetDatabaseSize();
        
        /// <summary>
        /// Optimize database performance
        /// </summary>
        Task OptimizeDatabaseAsync();
    }
}