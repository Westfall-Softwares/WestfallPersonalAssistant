using System;
using System.Collections.Generic;
using System.Data;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace WestfallPersonalAssistant.Services
{
    public class DatabaseService : IDatabaseService
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly string _connectionString;
        
        public DatabaseService(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService;
            var dbPath = Path.Combine(_fileSystemService.GetAppDataPath(), "westfall_assistant.db");
            _connectionString = $"Data Source={dbPath}";
        }
        
        public async Task InitializeAsync()
        {
            try
            {
                // Ensure the directory exists
                var dbPath = GetDatabasePath();
                var directory = Path.GetDirectoryName(dbPath);
                if (!string.IsNullOrEmpty(directory))
                {
                    _fileSystemService.CreateDirectory(directory);
                }
                
                using var connection = new SqliteConnection(_connectionString);
                await connection.OpenAsync();
                
                // Create tables
                await CreateTablesAsync(connection);
                
                Console.WriteLine("Database initialized successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing database: {ex.Message}");
                throw;
            }
        }
        
        private async Task CreateTablesAsync(SqliteConnection connection)
        {
            var createTables = new[]
            {
                // Business Tasks table
                @"CREATE TABLE IF NOT EXISTS BusinessTasks (
                    Id TEXT PRIMARY KEY,
                    Title TEXT NOT NULL,
                    Description TEXT,
                    DueDate TEXT,
                    Category TEXT,
                    IsCompleted INTEGER DEFAULT 0,
                    Priority INTEGER DEFAULT 0,
                    CreatedDate TEXT,
                    CompletedDate TEXT,
                    Status TEXT DEFAULT 'Pending',
                    AssignedTo TEXT,
                    EstimatedHours REAL DEFAULT 0,
                    ActualHours REAL DEFAULT 0,
                    Tags TEXT,
                    BusinessImpact TEXT DEFAULT 'Medium',
                    ProjectId TEXT,
                    ClientId TEXT,
                    TaskType INTEGER DEFAULT 0,
                    RevenueImpact REAL,
                    StrategicImportance INTEGER DEFAULT 2
                )",
                
                // Settings table
                @"CREATE TABLE IF NOT EXISTS Settings (
                    Key TEXT PRIMARY KEY,
                    Value TEXT,
                    LastModified TEXT
                )",
                
                // TailorPack information table
                @"CREATE TABLE IF NOT EXISTS TailorPacks (
                    Id TEXT PRIMARY KEY,
                    Name TEXT NOT NULL,
                    Description TEXT,
                    Version TEXT,
                    Author TEXT,
                    SupportedPlatforms TEXT,
                    Dependencies TEXT,
                    IsEnabled INTEGER DEFAULT 1,
                    InstallDate TEXT,
                    LastUsed TEXT
                )",
                
                // Business goals table
                @"CREATE TABLE IF NOT EXISTS BusinessGoals (
                    Id TEXT PRIMARY KEY,
                    Title TEXT NOT NULL,
                    Description TEXT,
                    TargetValue REAL NOT NULL,
                    CurrentValue REAL DEFAULT 0,
                    Unit TEXT,
                    Category TEXT,
                    StartDate TEXT,
                    TargetDate TEXT,
                    IsCompleted INTEGER DEFAULT 0,
                    CreatedDate TEXT,
                    CompletedDate TEXT,
                    GoalType INTEGER DEFAULT 0,
                    Priority INTEGER DEFAULT 2
                )",
                
                // Analytics data table
                @"CREATE TABLE IF NOT EXISTS AnalyticsData (
                    Id TEXT PRIMARY KEY,
                    Date TEXT,
                    MetricType TEXT,
                    MetricName TEXT,
                    Value REAL,
                    AdditionalData TEXT
                )"
            };
            
            foreach (var sql in createTables)
            {
                using var command = new SqliteCommand(sql, connection);
                await command.ExecuteNonQueryAsync();
            }
        }
        
        public async Task<int> ExecuteNonQueryAsync(string sql, params object[] parameters)
        {
            using var connection = new SqliteConnection(_connectionString);
            await connection.OpenAsync();
            
            using var command = new SqliteCommand(sql, connection);
            AddParameters(command, parameters);
            
            return await command.ExecuteNonQueryAsync();
        }
        
        public async Task<T?> ExecuteScalarAsync<T>(string sql, params object[] parameters) where T : struct
        {
            using var connection = new SqliteConnection(_connectionString);
            await connection.OpenAsync();
            
            using var command = new SqliteCommand(sql, connection);
            AddParameters(command, parameters);
            
            var result = await command.ExecuteScalarAsync();
            
            if (result == null || result == DBNull.Value)
                return default(T);
                
            return (T)Convert.ChangeType(result, typeof(T));
        }
        
        public async Task<T[]> QueryAsync<T>(string sql, Func<object[], T> mapper, params object[] parameters)
        {
            var results = new List<T>();
            
            using var connection = new SqliteConnection(_connectionString);
            await connection.OpenAsync();
            
            using var command = new SqliteCommand(sql, connection);
            AddParameters(command, parameters);
            
            using var reader = await command.ExecuteReaderAsync();
            
            while (await reader.ReadAsync())
            {
                var values = new object[reader.FieldCount];
                reader.GetValues(values);
                results.Add(mapper(values));
            }
            
            return results.ToArray();
        }
        
        private void AddParameters(SqliteCommand command, object[] parameters)
        {
            for (int i = 0; i < parameters.Length; i++)
            {
                var parameter = command.CreateParameter();
                parameter.ParameterName = $"@p{i}";
                parameter.Value = parameters[i] ?? DBNull.Value;
                command.Parameters.Add(parameter);
            }
        }
        
        public bool DatabaseExists()
        {
            var dbPath = GetDatabasePath();
            return _fileSystemService.FileExists(dbPath);
        }
        
        public Task<bool> BackupDatabaseAsync(string backupPath)
        {
            try
            {
                var dbPath = GetDatabasePath();
                if (!_fileSystemService.FileExists(dbPath))
                    return Task.FromResult(false);
                
                _fileSystemService.CopyFile(dbPath, backupPath, true);
                
                // Verify backup
                return Task.FromResult(_fileSystemService.FileExists(backupPath));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error backing up database: {ex.Message}");
                return Task.FromResult(false);
            }
        }
        
        public async Task<bool> RestoreDatabaseAsync(string backupPath)
        {
            try
            {
                if (!_fileSystemService.FileExists(backupPath))
                    return false;
                
                var dbPath = GetDatabasePath();
                _fileSystemService.CopyFile(backupPath, dbPath, true);
                
                // Verify restore by trying to open the database
                using var connection = new SqliteConnection(_connectionString);
                await connection.OpenAsync();
                
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error restoring database: {ex.Message}");
                return false;
            }
        }
        
        public long GetDatabaseSize()
        {
            var dbPath = GetDatabasePath();
            return _fileSystemService.FileExists(dbPath) ? _fileSystemService.GetFileSize(dbPath) : 0;
        }
        
        public async Task OptimizeDatabaseAsync()
        {
            try
            {
                using var connection = new SqliteConnection(_connectionString);
                await connection.OpenAsync();
                
                // Run VACUUM to optimize database
                using var command = new SqliteCommand("VACUUM", connection);
                await command.ExecuteNonQueryAsync();
                
                // Analyze tables for better query planning
                using var analyzeCommand = new SqliteCommand("ANALYZE", connection);
                await analyzeCommand.ExecuteNonQueryAsync();
                
                Console.WriteLine("Database optimization completed");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error optimizing database: {ex.Message}");
            }
        }
        
        private string GetDatabasePath()
        {
            return Path.Combine(_fileSystemService.GetAppDataPath(), "westfall_assistant.db");
        }
    }
}