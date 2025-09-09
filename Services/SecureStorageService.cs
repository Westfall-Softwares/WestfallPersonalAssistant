using System;
using System.Security.Cryptography;
using System.Text;
using System.IO;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for secure storage of sensitive data with encryption
    /// </summary>
    public interface ISecureStorageService
    {
        // Encryption/Decryption methods
        string EncryptString(string plainText);
        string DecryptString(string cipherText);
        
        // Secure storage methods
        void StoreSecureData(string key, string data);
        string RetrieveSecureData(string key);
        void DeleteSecureData(string key);
        bool SecureDataExists(string key);
        
        // Key management
        void GenerateNewKey();
        void RotateKeys();
        
        // Secure deletion
        void SecureDeleteFile(string filePath);
        void SecureDeleteData(byte[] data);
    }
    
    /// <summary>
    /// Implementation of secure storage service using AES encryption
    /// </summary>
    public class SecureStorageService : ISecureStorageService, IDisposable
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly ISettingsManager _settingsManager;
        private readonly string _secureStoragePath;
        private readonly string _keyFile;
        private byte[] _encryptionKey;
        private bool _disposed = false;
        
        public SecureStorageService(IFileSystemService fileSystemService, ISettingsManager settingsManager)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            _settingsManager = settingsManager ?? throw new ArgumentNullException(nameof(settingsManager));
            
            _secureStoragePath = Path.Combine(_fileSystemService.GetAppDataPath(), "secure");
            _keyFile = Path.Combine(_secureStoragePath, ".keystore");
            
            EnsureSecureStorageDirectory();
            InitializeEncryption();
        }
        
        private void EnsureSecureStorageDirectory()
        {
            if (!Directory.Exists(_secureStoragePath))
            {
                Directory.CreateDirectory(_secureStoragePath);
                
                // Set restrictive permissions on the secure storage directory
                try
                {
                    var dirInfo = new DirectoryInfo(_secureStoragePath);
                    // Platform-specific permission setting would go here
                    // For now, we'll rely on the OS default permissions
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Warning: Could not set secure directory permissions: {ex.Message}");
                }
            }
        }
        
        private void InitializeEncryption()
        {
            if (File.Exists(_keyFile))
            {
                try
                {
                    // Load existing key (in a real implementation, this would be more secure)
                    var keyData = File.ReadAllBytes(_keyFile);
                    _encryptionKey = ProtectKey(keyData);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error loading encryption key: {ex.Message}");
                    GenerateNewKey();
                }
            }
            else
            {
                GenerateNewKey();
            }
        }
        
        public void GenerateNewKey()
        {
            using (var rng = RandomNumberGenerator.Create())
            {
                _encryptionKey = new byte[32]; // 256-bit key
                rng.GetBytes(_encryptionKey);
                
                // Store the key securely (in a real implementation, use platform keystore)
                var protectedKey = UnprotectKey(_encryptionKey);
                File.WriteAllBytes(_keyFile, protectedKey);
                
                // Set restrictive file permissions
                try
                {
                    var fileInfo = new FileInfo(_keyFile);
                    // Platform-specific permission setting would go here
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Warning: Could not set key file permissions: {ex.Message}");
                }
            }
        }
        
        public void RotateKeys()
        {
            // In a real implementation, this would:
            // 1. Generate new key
            // 2. Re-encrypt all stored data with new key
            // 3. Securely delete old key
            
            var oldKey = _encryptionKey;
            GenerateNewKey();
            
            // Securely delete old key
            SecureDeleteData(oldKey);
        }
        
        public string EncryptString(string plainText)
        {
            if (string.IsNullOrEmpty(plainText))
                return string.Empty;
                
            try
            {
                using (var aes = Aes.Create())
                {
                    aes.Key = _encryptionKey;
                    aes.GenerateIV();
                    
                    using (var encryptor = aes.CreateEncryptor())
                    using (var msEncrypt = new MemoryStream())
                    {
                        // Prepend IV to the encrypted data
                        msEncrypt.Write(aes.IV, 0, aes.IV.Length);
                        
                        using (var csEncrypt = new CryptoStream(msEncrypt, encryptor, CryptoStreamMode.Write))
                        using (var swEncrypt = new StreamWriter(csEncrypt))
                        {
                            swEncrypt.Write(plainText);
                        }
                        
                        return Convert.ToBase64String(msEncrypt.ToArray());
                    }
                }
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Encryption failed: {ex.Message}", ex);
            }
        }
        
        public string DecryptString(string cipherText)
        {
            if (string.IsNullOrEmpty(cipherText))
                return string.Empty;
                
            try
            {
                var fullCipher = Convert.FromBase64String(cipherText);
                
                using (var aes = Aes.Create())
                {
                    aes.Key = _encryptionKey;
                    
                    // Extract IV from the beginning of the cipher text
                    var iv = new byte[aes.BlockSize / 8];
                    var cipher = new byte[fullCipher.Length - iv.Length];
                    
                    Array.Copy(fullCipher, 0, iv, 0, iv.Length);
                    Array.Copy(fullCipher, iv.Length, cipher, 0, cipher.Length);
                    
                    aes.IV = iv;
                    
                    using (var decryptor = aes.CreateDecryptor())
                    using (var msDecrypt = new MemoryStream(cipher))
                    using (var csDecrypt = new CryptoStream(msDecrypt, decryptor, CryptoStreamMode.Read))
                    using (var srDecrypt = new StreamReader(csDecrypt))
                    {
                        return srDecrypt.ReadToEnd();
                    }
                }
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Decryption failed: {ex.Message}", ex);
            }
        }
        
        public void StoreSecureData(string key, string data)
        {
            if (string.IsNullOrEmpty(key))
                throw new ArgumentException("Key cannot be null or empty", nameof(key));
                
            var encryptedData = EncryptString(data);
            var sanitizedKey = SanitizeFileName(key);
            var filePath = Path.Combine(_secureStoragePath, $"{sanitizedKey}.secure");
            
            File.WriteAllText(filePath, encryptedData);
        }
        
        public string RetrieveSecureData(string key)
        {
            if (string.IsNullOrEmpty(key))
                throw new ArgumentException("Key cannot be null or empty", nameof(key));
                
            var sanitizedKey = SanitizeFileName(key);
            var filePath = Path.Combine(_secureStoragePath, $"{sanitizedKey}.secure");
            
            if (!File.Exists(filePath))
                return null;
                
            var encryptedData = File.ReadAllText(filePath);
            return DecryptString(encryptedData);
        }
        
        public void DeleteSecureData(string key)
        {
            if (string.IsNullOrEmpty(key))
                throw new ArgumentException("Key cannot be null or empty", nameof(key));
                
            var sanitizedKey = SanitizeFileName(key);
            var filePath = Path.Combine(_secureStoragePath, $"{sanitizedKey}.secure");
            
            if (File.Exists(filePath))
            {
                SecureDeleteFile(filePath);
            }
        }
        
        public bool SecureDataExists(string key)
        {
            if (string.IsNullOrEmpty(key))
                return false;
                
            var sanitizedKey = SanitizeFileName(key);
            var filePath = Path.Combine(_secureStoragePath, $"{sanitizedKey}.secure");
            
            return File.Exists(filePath);
        }
        
        public void SecureDeleteFile(string filePath)
        {
            if (!File.Exists(filePath))
                return;
                
            try
            {
                // Simple secure deletion - overwrite with random data
                var fileInfo = new FileInfo(filePath);
                var fileSize = fileInfo.Length;
                
                using (var rng = RandomNumberGenerator.Create())
                using (var fs = new FileStream(filePath, FileMode.Open, FileAccess.Write))
                {
                    // Overwrite with random data 3 times
                    for (int pass = 0; pass < 3; pass++)
                    {
                        fs.Seek(0, SeekOrigin.Begin);
                        var buffer = new byte[4096];
                        
                        for (long written = 0; written < fileSize; written += buffer.Length)
                        {
                            var bytesToWrite = (int)Math.Min(buffer.Length, fileSize - written);
                            rng.GetBytes(buffer);
                            fs.Write(buffer, 0, bytesToWrite);
                        }
                        
                        fs.Flush();
                    }
                }
                
                // Finally delete the file
                File.Delete(filePath);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Warning: Secure file deletion failed: {ex.Message}");
                // Fall back to normal deletion
                try
                {
                    File.Delete(filePath);
                }
                catch
                {
                    // If we can't delete it, at least we overwrote it
                }
            }
        }
        
        public void SecureDeleteData(byte[] data)
        {
            if (data == null)
                return;
                
            // Overwrite sensitive data in memory
            using (var rng = RandomNumberGenerator.Create())
            {
                rng.GetBytes(data);
                Array.Clear(data, 0, data.Length);
            }
        }
        
        private string SanitizeFileName(string fileName)
        {
            var invalidChars = Path.GetInvalidFileNameChars();
            var sanitized = fileName;
            
            foreach (var c in invalidChars)
            {
                sanitized = sanitized.Replace(c, '_');
            }
            
            return sanitized;
        }
        
        private byte[] ProtectKey(byte[] key)
        {
            // In a real implementation, use platform-specific protection
            // For now, return as-is (not secure!)
            return key;
        }
        
        private byte[] UnprotectKey(byte[] protectedKey)
        {
            // In a real implementation, use platform-specific unprotection
            // For now, return as-is (not secure!)
            return protectedKey;
        }
        
        public void Dispose()
        {
            if (!_disposed)
            {
                if (_encryptionKey != null)
                {
                    SecureDeleteData(_encryptionKey);
                    _encryptionKey = null;
                }
                
                _disposed = true;
            }
        }
    }
}