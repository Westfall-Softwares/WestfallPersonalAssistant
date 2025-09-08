using System;
using System.Collections.Generic;
using System.Linq;

namespace WestfallPersonalAssistant.TailorPack
{
    public class FeatureRegistry
    {
        private readonly Dictionary<string, IFeature> _features = new();
        private readonly Dictionary<string, string> _featureToPackMapping = new();
        
        public event EventHandler<FeatureEventArgs>? FeatureRegistered;
        public event EventHandler<FeatureEventArgs>? FeatureUnregistered;
        public event EventHandler<FeatureConflictEventArgs>? FeatureConflict;
        
        /// <summary>
        /// Register a feature from a pack
        /// </summary>
        public bool RegisterFeature(IFeature feature, string packId)
        {
            if (feature == null || string.IsNullOrEmpty(feature.Id))
                return false;
                
            // Check for conflicts
            if (_features.ContainsKey(feature.Id))
            {
                var existingPackId = _featureToPackMapping[feature.Id];
                var conflictArgs = new FeatureConflictEventArgs(feature.Id, existingPackId, packId);
                FeatureConflict?.Invoke(this, conflictArgs);
                
                if (!conflictArgs.AllowOverride)
                    return false;
                    
                // Unregister existing feature first
                UnregisterFeature(feature.Id);
            }
            
            _features[feature.Id] = feature;
            _featureToPackMapping[feature.Id] = packId;
            
            FeatureRegistered?.Invoke(this, new FeatureEventArgs(feature, packId));
            return true;
        }
        
        /// <summary>
        /// Unregister a feature
        /// </summary>
        public bool UnregisterFeature(string featureId)
        {
            if (!_features.TryGetValue(featureId, out var feature))
                return false;
                
            var packId = _featureToPackMapping[featureId];
            
            _features.Remove(featureId);
            _featureToPackMapping.Remove(featureId);
            
            FeatureUnregistered?.Invoke(this, new FeatureEventArgs(feature, packId));
            return true;
        }
        
        /// <summary>
        /// Unregister all features from a specific pack
        /// </summary>
        public void UnregisterPackFeatures(string packId)
        {
            var featuresToRemove = _featureToPackMapping
                .Where(kvp => kvp.Value == packId)
                .Select(kvp => kvp.Key)
                .ToList();
                
            foreach (var featureId in featuresToRemove)
            {
                UnregisterFeature(featureId);
            }
        }
        
        /// <summary>
        /// Get a feature by ID
        /// </summary>
        public IFeature? GetFeature(string featureId)
        {
            _features.TryGetValue(featureId, out var feature);
            return feature;
        }
        
        /// <summary>
        /// Get all registered features
        /// </summary>
        public IFeature[] GetAllFeatures()
        {
            return _features.Values.ToArray();
        }
        
        /// <summary>
        /// Get features by pack ID
        /// </summary>
        public IFeature[] GetFeaturesByPack(string packId)
        {
            return _featureToPackMapping
                .Where(kvp => kvp.Value == packId)
                .Select(kvp => _features[kvp.Key])
                .ToArray();
        }
        
        /// <summary>
        /// Check if a feature is registered
        /// </summary>
        public bool IsFeatureRegistered(string featureId)
        {
            return _features.ContainsKey(featureId);
        }
        
        /// <summary>
        /// Get the pack ID that owns a feature
        /// </summary>
        public string? GetFeatureOwner(string featureId)
        {
            _featureToPackMapping.TryGetValue(featureId, out var packId);
            return packId;
        }
    }
    
    public class FeatureEventArgs : EventArgs
    {
        public IFeature Feature { get; }
        public string PackId { get; }
        
        public FeatureEventArgs(IFeature feature, string packId)
        {
            Feature = feature;
            PackId = packId;
        }
    }
    
    public class FeatureConflictEventArgs : EventArgs
    {
        public string FeatureId { get; }
        public string ExistingPackId { get; }
        public string NewPackId { get; }
        public bool AllowOverride { get; set; }
        
        public FeatureConflictEventArgs(string featureId, string existingPackId, string newPackId)
        {
            FeatureId = featureId;
            ExistingPackId = existingPackId;
            NewPackId = newPackId;
            AllowOverride = false;
        }
    }
}