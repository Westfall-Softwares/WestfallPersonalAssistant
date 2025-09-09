using System.Collections.Generic;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    public interface IFileSystemService
    {
        /// <summary>
        /// Get the application data directory path
        /// </summary>
        string GetAppDataPath();
        
        /// <summary>
        /// Get the user documents directory path
        /// </summary>
        string GetDocumentsPath();
        
        /// <summary>
        /// Check if a file exists
        /// </summary>
        bool FileExists(string path);
        
        /// <summary>
        /// Check if a directory exists
        /// </summary>
        bool DirectoryExists(string path);
        
        /// <summary>
        /// Create a directory if it doesn't exist
        /// </summary>
        void CreateDirectory(string path);
        
        /// <summary>
        /// Read all text from a file
        /// </summary>
        Task<string> ReadAllTextAsync(string path);
        
        /// <summary>
        /// Write all text to a file
        /// </summary>
        Task WriteAllTextAsync(string path, string content);
        
        /// <summary>
        /// Delete a file
        /// </summary>
        void DeleteFile(string path);
        
        /// <summary>
        /// Delete a directory and all its contents
        /// </summary>
        void DeleteDirectory(string path, bool recursive = true);
        
        /// <summary>
        /// Get all files in a directory
        /// </summary>
        string[] GetFiles(string path, string searchPattern = "*", bool recursive = false);
        
        /// <summary>
        /// Get all directories in a path
        /// </summary>
        string[] GetDirectories(string path);
        
        /// <summary>
        /// Get file size in bytes
        /// </summary>
        long GetFileSize(string path);
        
        /// <summary>
        /// Copy a file
        /// </summary>
        void CopyFile(string sourcePath, string destinationPath, bool overwrite = false);
        
        /// <summary>
        /// Move a file
        /// </summary>
        void MoveFile(string sourcePath, string destinationPath);
        
        /// <summary>
        /// Get the Tailor Packs directory
        /// </summary>
        string GetTailorPacksPath();
        
        /// <summary>
        /// Get the settings file path
        /// </summary>
        string GetSettingsPath();
        
        /// <summary>
        /// Get the logs directory path
        /// </summary>
        string GetLogsPath();
    }
}