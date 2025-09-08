using System;
using System.Collections.Generic;
using System.Linq;

namespace WestfallPersonalAssistant.TailorPack
{
    public class FeatureActivationService
    {
        private readonly FeatureRegistry _featureRegistry;
        private readonly HashSet<string> _activeFeatures = new();
        private readonly Dictionary<string, List<string>> _featureDependencies = new();
        
        public event EventHandler<FeatureActivationEventArgs>? FeatureActivated;
        public event EventHandler<FeatureActivationEventArgs>? FeatureDeactivated;
        public event EventHandler<FeatureActivationErrorEventArgs>? ActivationError;
        
        public FeatureActivationService(FeatureRegistry featureRegistry)
        {
            _featureRegistry = featureRegistry;
        }
        
        /// <summary>
        /// Activate a feature and its dependencies
        /// </summary>
        public bool ActivateFeature(string featureId)
        {
            try
            {
                if (_activeFeatures.Contains(featureId))
                    return true; // Already active
                    
                var feature = _featureRegistry.GetFeature(featureId);
                if (feature == null)
                {
                    var error = new FeatureActivationErrorEventArgs(featureId, "Feature not found");
                    ActivationError?.Invoke(this, error);
                    return false;
                }
                
                // Check and activate dependencies first
                if (_featureDependencies.ContainsKey(featureId))
                {
                    foreach (var dependency in _featureDependencies[featureId])
                    {
                        if (!ActivateFeature(dependency))
                        {
                            var error = new FeatureActivationErrorEventArgs(featureId, $"Failed to activate dependency: {dependency}");
                            ActivationError?.Invoke(this, error);
                            return false;
                        }
                    }
                }
                
                // Initialize the feature
                feature.Initialize();
                _activeFeatures.Add(featureId);
                
                FeatureActivated?.Invoke(this, new FeatureActivationEventArgs(featureId, feature));
                return true;
            }
            catch (Exception ex)
            {
                var error = new FeatureActivationErrorEventArgs(featureId, $"Exception during activation: {ex.Message}");
                ActivationError?.Invoke(this, error);
                return false;
            }
        }
        
        /// <summary>
        /// Deactivate a feature and handle dependents
        /// </summary>
        public bool DeactivateFeature(string featureId)
        {
            try
            {
                if (!_activeFeatures.Contains(featureId))
                    return true; // Already inactive
                    
                var feature = _featureRegistry.GetFeature(featureId);
                if (feature == null)
                    return false;
                
                // Check if any active features depend on this one
                var dependents = GetActiveDependents(featureId);
                if (dependents.Any())
                {
                    var error = new FeatureActivationErrorEventArgs(featureId, 
                        $"Cannot deactivate: features {string.Join(", ", dependents)} depend on this feature");
                    ActivationError?.Invoke(this, error);
                    return false;
                }
                
                // Shutdown the feature
                feature.Shutdown();
                _activeFeatures.Remove(featureId);
                
                FeatureDeactivated?.Invoke(this, new FeatureActivationEventArgs(featureId, feature));
                return true;
            }
            catch (Exception ex)
            {
                var error = new FeatureActivationErrorEventArgs(featureId, $"Exception during deactivation: {ex.Message}");
                ActivationError?.Invoke(this, error);
                return false;
            }
        }
        
        /// <summary>
        /// Set dependencies for a feature
        /// </summary>
        public void SetFeatureDependencies(string featureId, string[] dependencies)
        {
            _featureDependencies[featureId] = dependencies.ToList();
        }
        
        /// <summary>
        /// Check if a feature is active
        /// </summary>
        public bool IsFeatureActive(string featureId)
        {
            return _activeFeatures.Contains(featureId);
        }
        
        /// <summary>
        /// Get all active features
        /// </summary>
        public string[] GetActiveFeatures()
        {
            return _activeFeatures.ToArray();
        }
        
        /// <summary>
        /// Get features that depend on the specified feature
        /// </summary>
        private string[] GetActiveDependents(string featureId)
        {
            return _featureDependencies
                .Where(kvp => kvp.Value.Contains(featureId) && _activeFeatures.Contains(kvp.Key))
                .Select(kvp => kvp.Key)
                .ToArray();
        }
        
        /// <summary>
        /// Deactivate all features from a pack
        /// </summary>
        public void DeactivatePackFeatures(string packId)
        {
            var packFeatures = _featureRegistry.GetFeaturesByPack(packId);
            foreach (var feature in packFeatures)
            {
                if (_activeFeatures.Contains(feature.Id))
                {
                    DeactivateFeature(feature.Id);
                }
            }
        }
        
        /// <summary>
        /// Activate all features from a pack
        /// </summary>
        public bool ActivatePackFeatures(string packId)
        {
            var packFeatures = _featureRegistry.GetFeaturesByPack(packId);
            foreach (var feature in packFeatures)
            {
                if (!ActivateFeature(feature.Id))
                {
                    // If any feature fails to activate, deactivate any that were activated
                    DeactivatePackFeatures(packId);
                    return false;
                }
            }
            return true;
        }
    }
    
    public class FeatureActivationEventArgs : EventArgs
    {
        public string FeatureId { get; }
        public IFeature Feature { get; }
        
        public FeatureActivationEventArgs(string featureId, IFeature feature)
        {
            FeatureId = featureId;
            Feature = feature;
        }
    }
    
    public class FeatureActivationErrorEventArgs : EventArgs
    {
        public string FeatureId { get; }
        public string Error { get; }
        
        public FeatureActivationErrorEventArgs(string featureId, string error)
        {
            FeatureId = featureId;
            Error = error;
        }
    }
}