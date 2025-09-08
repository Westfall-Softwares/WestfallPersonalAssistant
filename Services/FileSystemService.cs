using System;
using System.IO;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Platform;

namespace WestfallPersonalAssistant.Services
{
    public class FileSystemService : IFileSystemService
    {
        private readonly IPlatformService _platformService;
        
        public FileSystemService(IPlatformService platformService)
        {
            _platformService = platformService;
            InitializeDirectories();
        }
        
        private void InitializeDirectories()
        {
            // Ensure all required directories exist
            CreateDirectory(GetAppDataPath());
            CreateDirectory(GetTailorPacksPath());
            CreateDirectory(GetLogsPath());
        }
        
        public string GetAppDataPath()
        {
            return _platformService.GetAppDataPath();
        }
        
        public string GetDocumentsPath()
        {
            return Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
        }
        
        public string GetTailorPacksPath()
        {
            return Path.Combine(GetAppDataPath(), "TailorPacks");
        }
        
        public string GetSettingsPath()
        {
            return Path.Combine(GetAppDataPath(), "settings.json");
        }
        
        public string GetLogsPath()
        {
            return Path.Combine(GetAppDataPath(), "Logs");
        }
        
        public bool FileExists(string path)
        {
            return File.Exists(path);
        }
        
        public bool DirectoryExists(string path)
        {
            return Directory.Exists(path);
        }
        
        public void CreateDirectory(string path)
        {
            if (!Directory.Exists(path))
            {
                Directory.CreateDirectory(path);
            }
        }
        
        public async Task<string> ReadAllTextAsync(string path)
        {
            return await File.ReadAllTextAsync(path);
        }
        
        public async Task WriteAllTextAsync(string path, string content)
        {
            // Ensure directory exists
            var directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            await File.WriteAllTextAsync(path, content);
        }
        
        public void DeleteFile(string path)
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        
        public void DeleteDirectory(string path, bool recursive = true)
        {
            if (Directory.Exists(path))
            {
                Directory.Delete(path, recursive);
            }
        }
        
        public string[] GetFiles(string path, string searchPattern = "*", bool recursive = false)
        {
            if (!Directory.Exists(path))
                return Array.Empty<string>();
                
            var searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
            return Directory.GetFiles(path, searchPattern, searchOption);
        }
        
        public string[] GetDirectories(string path)
        {
            if (!Directory.Exists(path))
                return Array.Empty<string>();
                
            return Directory.GetDirectories(path);
        }
        
        public long GetFileSize(string path)
        {
            if (!File.Exists(path))
                return 0;
                
            var fileInfo = new FileInfo(path);
            return fileInfo.Length;
        }
        
        public void CopyFile(string sourcePath, string destinationPath, bool overwrite = false)
        {
            // Ensure destination directory exists
            var directory = Path.GetDirectoryName(destinationPath);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            File.Copy(sourcePath, destinationPath, overwrite);
        }
        
        public void MoveFile(string sourcePath, string destinationPath)
        {
            // Ensure destination directory exists
            var directory = Path.GetDirectoryName(destinationPath);
            if (!string.IsNullOrEmpty(directory))
            {
                CreateDirectory(directory);
            }
            
            File.Move(sourcePath, destinationPath);
        }
    }
}