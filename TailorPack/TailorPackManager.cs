using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.TailorPack
{
    public class TailorPackManager
    {
        private static TailorPackManager? _instance;
        private readonly Dictionary<string, ITailorPack> _loadedPacks = new();
        private readonly FeatureRegistry _featureRegistry;
        private readonly FeatureActivationService _activationService;
        private IFileSystemService? _fileSystemService;
        private IOrderVerificationService? _orderVerificationService;
        
        public static TailorPackManager Instance 
        {
            get 
            {
                _instance ??= new TailorPackManager();
                return _instance;
            }
        }
        
        public FeatureRegistry FeatureRegistry => _featureRegistry;
        public FeatureActivationService ActivationService => _activationService;
        
        public event EventHandler<PackEventArgs>? PackLoaded;
        public event EventHandler<PackEventArgs>? PackUnloaded;
        public event EventHandler<PackErrorEventArgs>? PackError;
        
        private TailorPackManager()
        {
            _featureRegistry = new FeatureRegistry();
            _activationService = new FeatureActivationService(_featureRegistry);
        }
        
        public void Initialize(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService;
            _orderVerificationService = new OrderVerificationService(fileSystemService);
            DiscoverPacks();
        }
        
        public void DiscoverPacks()
        {
            if (_fileSystemService == null) return;
            
            try
            {
                var packsPath = _fileSystemService.GetTailorPacksPath();
                Console.WriteLine($"Discovering packs in: {packsPath}");
                
                if (!_fileSystemService.DirectoryExists(packsPath))
                {
                    _fileSystemService.CreateDirectory(packsPath);
                    return;
                }
                
                var packDirectories = _fileSystemService.GetDirectories(packsPath);
                foreach (var packDir in packDirectories)
                {
                    var packId = Path.GetFileName(packDir);
                    Console.WriteLine($"Found pack directory: {packId}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error discovering packs: {ex.Message}");
                PackError?.Invoke(this, new PackErrorEventArgs("discovery", $"Pack discovery failed: {ex.Message}"));
            }
        }
        
        public bool LoadPack(string packId)
        {
            try
            {
                if (_loadedPacks.ContainsKey(packId))
                {
                    Console.WriteLine($"Pack {packId} is already loaded");
                    return true;
                }
                
                Console.WriteLine($"Loading pack: {packId}");
                
                // For now, we only support the demo pack
                if (packId == "marketing-essentials")
                {
                    var pack = new WestfallPersonalAssistant.Packs.Demo.MarketingEssentialsPack();
                    return LoadPackInstance(pack);
                }
                
                Console.WriteLine($"Pack {packId} not found or not supported");
                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading pack {packId}: {ex.Message}");
                PackError?.Invoke(this, new PackErrorEventArgs(packId, $"Load failed: {ex.Message}"));
                return false;
            }
        }

        /// <summary>
        /// Asynchronously load pack to avoid blocking UI thread
        /// </summary>
        public async Task<bool> LoadPackAsync(string packId, IProgress<ProgressInfo>? progress = null)
        {
            return await Task.Run(async () =>
            {
                try
                {
                    progress?.Report(new ProgressInfo(0, $"Checking pack {packId}..."));
                    
                    if (_loadedPacks.ContainsKey(packId))
                    {
                        Console.WriteLine($"Pack {packId} is already loaded");
                        progress?.Report(new ProgressInfo(100, "Pack already loaded"));
                        return true;
                    }
                    
                    progress?.Report(new ProgressInfo(25, $"Initializing pack {packId}..."));
                    Console.WriteLine($"Loading pack: {packId}");
                    
                    // Simulate some loading work
                    await Task.Delay(100);
                    
                    progress?.Report(new ProgressInfo(50, "Creating pack instance..."));
                    
                    // For now, we only support the demo pack
                    if (packId == "marketing-essentials")
                    {
                        var pack = new WestfallPersonalAssistant.Packs.Demo.MarketingEssentialsPack();
                        
                        progress?.Report(new ProgressInfo(75, "Loading pack features..."));
                        await Task.Delay(50); // Simulate feature loading
                        
                        bool result = LoadPackInstance(pack);
                        
                        progress?.Report(new ProgressInfo(100, result ? "Pack loaded successfully" : "Pack load failed"));
                        return result;
                    }
                    
                    Console.WriteLine($"Pack {packId} not found or not supported");
                    progress?.Report(new ProgressInfo(100, "Pack not found"));
                    return false;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error loading pack {packId}: {ex.Message}");
                    progress?.Report(new ProgressInfo(100, $"Error: {ex.Message}"));
                    PackError?.Invoke(this, new PackErrorEventArgs(packId, $"Load failed: {ex.Message}"));
                    return false;
                }
            });
        }
        
        private bool LoadPackInstance(ITailorPack pack)
        {
            try
            {
                var manifest = pack.GetManifest();
                
                if (string.IsNullOrEmpty(manifest.Id))
                {
                    Console.WriteLine("Pack manifest has no ID");
                    return false;
                }
                
                if (_loadedPacks.ContainsKey(manifest.Id))
                {
                    Console.WriteLine($"Pack {manifest.Id} is already loaded");
                    return true;
                }
                
                // Initialize the pack
                pack.Initialize();
                
                // Register features
                var features = pack.GetFeatures();
                foreach (var feature in features)
                {
                    _featureRegistry.RegisterFeature(feature, manifest.Id);
                }
                
                _loadedPacks[manifest.Id] = pack;
                PackLoaded?.Invoke(this, new PackEventArgs(manifest.Id, pack));
                
                Console.WriteLine($"Pack {manifest.Id} loaded successfully with {features.Length} features");
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading pack instance: {ex.Message}");
                return false;
            }
        }
        
        public void UnloadPack(string packId)
        {
            try
            {
                if (_loadedPacks.TryGetValue(packId, out var pack))
                {
                    // Deactivate all features from this pack
                    _activationService.DeactivatePackFeatures(packId);
                    
                    // Unregister features
                    _featureRegistry.UnregisterPackFeatures(packId);
                    
                    // Shutdown the pack
                    pack.Shutdown();
                    _loadedPacks.Remove(packId);
                    
                    PackUnloaded?.Invoke(this, new PackEventArgs(packId, pack));
                    Console.WriteLine($"Pack {packId} unloaded successfully");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error unloading pack {packId}: {ex.Message}");
                PackError?.Invoke(this, new PackErrorEventArgs(packId, $"Unload failed: {ex.Message}"));
            }
        }
        
        public ITailorPack[] GetInstalledPacks()
        {
            return _loadedPacks.Values.ToArray();
        }
        
        public ITailorPack? GetPack(string packId)
        {
            _loadedPacks.TryGetValue(packId, out var pack);
            return pack;
        }
        
        public bool IsPackLoaded(string packId)
        {
            return _loadedPacks.ContainsKey(packId);
        }
        
        public bool ImportPack(string zipFilePath)
        {
            if (_fileSystemService == null) return false;
            
            try
            {
                Console.WriteLine($"Importing pack from: {zipFilePath}");
                
                if (!_fileSystemService.FileExists(zipFilePath))
                {
                    Console.WriteLine("Pack file does not exist");
                    return false;
                }
                
                var packsPath = _fileSystemService.GetTailorPacksPath();
                
                // Extract and validate the pack
                using var archive = ZipFile.OpenRead(zipFilePath);
                
                // Look for manifest file
                var manifestEntry = archive.Entries.FirstOrDefault(e => 
                    e.Name.Equals("manifest.json", StringComparison.OrdinalIgnoreCase));
                
                if (manifestEntry == null)
                {
                    Console.WriteLine("Pack does not contain a manifest.json file");
                    return false;
                }
                
                // Read and validate manifest
                using var manifestStream = manifestEntry.Open();
                using var reader = new StreamReader(manifestStream);
                var manifestJson = reader.ReadToEnd();
                
                var manifest = JsonSerializer.Deserialize<TailorPackManifest>(manifestJson);
                if (manifest == null || string.IsNullOrEmpty(manifest.Id))
                {
                    Console.WriteLine("Invalid manifest file");
                    return false;
                }
                
                // Extract to pack directory
                var packPath = Path.Combine(packsPath, manifest.Id);
                if (_fileSystemService.DirectoryExists(packPath))
                {
                    _fileSystemService.DeleteDirectory(packPath);
                }
                
                archive.ExtractToDirectory(packPath);
                Console.WriteLine($"Pack {manifest.Id} imported successfully");
                
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error importing pack: {ex.Message}");
                PackError?.Invoke(this, new PackErrorEventArgs("import", $"Import failed: {ex.Message}"));
                return false;
            }
        }
        
        public TailorPackManifest[] GetPackManifests()
        {
            return _loadedPacks.Values.Select(pack => pack.GetManifest()).ToArray();
        }
        
        /// <summary>
        /// Verify order number and attempt to activate pack
        /// </summary>
        public async Task<bool> VerifyAndActivatePackAsync(string orderNumber)
        {
            if (_orderVerificationService == null)
            {
                Console.WriteLine("Order verification service not initialized");
                return false;
            }
            
            try
            {
                var result = await _orderVerificationService.ValidateOrderAsync(orderNumber);
                if (result.IsValid && result.License != null)
                {
                    Console.WriteLine($"Order verified for pack: {result.License.PackId}");
                    
                    // Load and activate the pack
                    if (LoadPack(result.License.PackId))
                    {
                        return _activationService.ActivatePackFeatures(result.License.PackId);
                    }
                }
                else
                {
                    Console.WriteLine($"Order verification failed: {result.ErrorMessage}");
                    if (result.TrialAvailable)
                    {
                        Console.WriteLine("Trial version may be available");
                    }
                }
                
                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error verifying order: {ex.Message}");
                return false;
            }
        }
        
        /// <summary>
        /// Check if a pack is licensed
        /// </summary>
        public async Task<bool> IsPackLicensedAsync(string packId)
        {
            if (_orderVerificationService == null) return false;
            return await _orderVerificationService.IsPackLicensedAsync(packId);
        }
    }
    
    public class PackEventArgs : EventArgs
    {
        public string PackId { get; }
        public ITailorPack Pack { get; }
        
        public PackEventArgs(string packId, ITailorPack pack)
        {
            PackId = packId;
            Pack = pack;
        }
    }
    
    public class PackErrorEventArgs : EventArgs
    {
        public string PackId { get; }
        public string Error { get; }
        
        public PackErrorEventArgs(string packId, string error)
        {
            PackId = packId;
            Error = error;
        }
    }

    /// <summary>
    /// Progress information for long-running operations
    /// </summary>
    public class ProgressInfo
    {
        public int Percentage { get; }
        public string Message { get; }
        public TimeSpan? EstimatedTimeRemaining { get; }

        public ProgressInfo(int percentage, string message, TimeSpan? estimatedTimeRemaining = null)
        {
            Percentage = Math.Max(0, Math.Min(100, percentage));
            Message = message ?? string.Empty;
            EstimatedTimeRemaining = estimatedTimeRemaining;
        }
    }
}