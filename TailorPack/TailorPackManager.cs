using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace WestfallPersonalAssistant.TailorPack
{
    public class TailorPackManager
    {
        private static TailorPackManager? _instance;
        private readonly Dictionary<string, ITailorPack> _loadedPacks = new();
        
        public static TailorPackManager Instance 
        {
            get 
            {
                _instance ??= new TailorPackManager();
                return _instance;
            }
        }
        
        public void DiscoverPacks()
        {
            // Implementation will scan for packs in the designated directory
            Console.WriteLine("Discovering packs...");
        }
        
        public bool LoadPack(string packId)
        {
            // Implementation will load the pack assembly
            Console.WriteLine($"Loading pack: {packId}");
            return true;
        }
        
        public void UnloadPack(string packId)
        {
            if (_loadedPacks.TryGetValue(packId, out var pack))
            {
                pack.Shutdown();
                _loadedPacks.Remove(packId);
            }
        }
        
        public ITailorPack[] GetInstalledPacks()
        {
            return _loadedPacks.Values.ToArray();
        }
        
        public bool ImportPack(string zipFilePath)
        {
            // Implementation will extract and validate the pack
            Console.WriteLine($"Importing pack from: {zipFilePath}");
            return true;
        }
    }
}