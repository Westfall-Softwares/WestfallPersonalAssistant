using System;
using System.Threading.Tasks;
using WestfallPersonalAssistant.TailorPack;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for exporting large database files with progress tracking
    /// </summary>
    public class LargeDatabaseExportService
    {
        private readonly IDatabaseService _databaseService;
        private readonly IFileSystemService _fileSystemService;

        public LargeDatabaseExportService(IDatabaseService databaseService, IFileSystemService fileSystemService)
        {
            _databaseService = databaseService ?? throw new ArgumentNullException(nameof(databaseService));
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
        }

        /// <summary>
        /// Export database to file with progress reporting
        /// </summary>
        /// <param name="exportPath">Path where to export the database</param>
        /// <param name="progress">Progress reporter</param>
        /// <returns>True if export was successful</returns>
        public async Task<bool> ExportDatabaseAsync(string exportPath, IProgress<double>? progress = null)
        {
            try
            {
                // Convert IProgress<double> to IProgress<ProgressInfo>
                var progressInfo = progress != null ? new Progress<ProgressInfo>(info => 
                {
                    // Convert percentage to double (0.0 to 1.0)
                    progress.Report(info.Percentage / 100.0);
                }) : null;

                progress?.Report(0.0);

                // Step 1: Validate database exists (10%)
                if (!_databaseService.DatabaseExists())
                {
                    progress?.Report(1.0);
                    return false;
                }
                progress?.Report(0.1);

                // Step 2: Get database size for progress calculation (20%)
                var dbSize = _databaseService.GetDatabaseSize();
                progress?.Report(0.2);

                // Step 3: Optimize database before export (30%)
                await _databaseService.OptimizeDatabaseAsync();
                progress?.Report(0.3);

                // Step 4: Create backup/export (30% - 90%)
                var success = await _databaseService.BackupDatabaseAsync(exportPath);
                progress?.Report(0.9);

                // Step 5: Verify export (90% - 100%)
                if (success && _fileSystemService.FileExists(exportPath))
                {
                    var exportedSize = _fileSystemService.GetFileSize(exportPath);
                    success = exportedSize > 0;
                }

                progress?.Report(1.0);
                return success;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during database export: {ex.Message}");
                progress?.Report(1.0);
                return false;
            }
        }

        /// <summary>
        /// Export database with detailed progress information
        /// </summary>
        /// <param name="exportPath">Path where to export the database</param>
        /// <param name="progress">Detailed progress reporter</param>
        /// <returns>True if export was successful</returns>
        public async Task<bool> ExportDatabaseWithDetailedProgressAsync(string exportPath, IProgress<ProgressInfo>? progress = null)
        {
            try
            {
                progress?.Report(new ProgressInfo(0, "Starting database export..."));

                // Step 1: Validate database exists
                if (!_databaseService.DatabaseExists())
                {
                    progress?.Report(new ProgressInfo(100, "Database not found"));
                    return false;
                }
                progress?.Report(new ProgressInfo(10, "Database validation complete"));

                // Step 2: Get database information
                var dbSize = _databaseService.GetDatabaseSize();
                var dbSizeText = dbSize > 1024 * 1024 ? $"{dbSize / (1024 * 1024):N1} MB" : $"{dbSize / 1024:N1} KB";
                progress?.Report(new ProgressInfo(20, $"Database size: {dbSizeText}"));

                // Step 3: Optimize database
                progress?.Report(new ProgressInfo(25, "Optimizing database..."));
                await _databaseService.OptimizeDatabaseAsync();
                progress?.Report(new ProgressInfo(30, "Database optimization complete"));

                // Step 4: Export database
                progress?.Report(new ProgressInfo(35, "Starting export..."));
                var success = await _databaseService.BackupDatabaseAsync(exportPath);
                progress?.Report(new ProgressInfo(85, "Export complete"));

                // Step 5: Verify export
                progress?.Report(new ProgressInfo(90, "Verifying export..."));
                if (success && _fileSystemService.FileExists(exportPath))
                {
                    var exportedSize = _fileSystemService.GetFileSize(exportPath);
                    success = exportedSize > 0;
                    var exportSizeText = exportedSize > 1024 * 1024 ? $"{exportedSize / (1024 * 1024):N1} MB" : $"{exportedSize / 1024:N1} KB";
                    progress?.Report(new ProgressInfo(100, success ? $"Export successful ({exportSizeText})" : "Export verification failed"));
                }
                else
                {
                    progress?.Report(new ProgressInfo(100, "Export failed"));
                }

                return success;
            }
            catch (Exception ex)
            {
                progress?.Report(new ProgressInfo(100, $"Export failed: {ex.Message}"));
                Console.WriteLine($"Error during database export: {ex.Message}");
                return false;
            }
        }
    }
}