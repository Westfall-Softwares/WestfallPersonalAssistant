using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using System.Security.Cryptography;
using System.Text;

namespace WestfallPersonalAssistant.Services
{
    public class OrderVerificationService : IOrderVerificationService
    {
        private readonly IFileSystemService _fileSystemService;
        private readonly string _licensesPath;
        private readonly Dictionary<string, PackLicense> _activeLicenses = new();
        private readonly Dictionary<string, TrialLicense> _trialLicenses = new();

        public OrderVerificationService(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService;
            _licensesPath = Path.Combine(_fileSystemService.GetAppDataPath(), "licenses");
            _ = InitializeAsync();
        }

        private async Task InitializeAsync()
        {
            try
            {
                if (!_fileSystemService.DirectoryExists(_licensesPath))
                {
                    _fileSystemService.CreateDirectory(_licensesPath);
                }

                await LoadLicensesAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing order verification service: {ex.Message}");
            }
        }

        public async Task<OrderValidationResult> ValidateOrderAsync(string orderNumber)
        {
            try
            {
                // Basic format validation
                if (string.IsNullOrWhiteSpace(orderNumber) || orderNumber.Length < 8)
                {
                    return new OrderValidationResult
                    {
                        IsValid = false,
                        ErrorMessage = "Invalid order number format",
                        TrialAvailable = true
                    };
                }

                // In a real implementation, this would connect to a server
                // For now, we'll use a demo validation system
                var license = await CreateDemoLicenseAsync(orderNumber);
                
                if (license != null)
                {
                    _activeLicenses[license.PackId] = license;
                    await SaveLicensesAsync();
                    
                    return new OrderValidationResult
                    {
                        IsValid = true,
                        License = license,
                        TrialAvailable = false
                    };
                }

                return new OrderValidationResult
                {
                    IsValid = false,
                    ErrorMessage = "Order number not found or invalid",
                    TrialAvailable = true
                };
            }
            catch (Exception ex)
            {
                return new OrderValidationResult
                {
                    IsValid = false,
                    ErrorMessage = $"Validation error: {ex.Message}",
                    TrialAvailable = true
                };
            }
        }

        public async Task<PackLicense?> GetLicenseAsync(string packId)
        {
            await LoadLicensesAsync();
            _activeLicenses.TryGetValue(packId, out var license);
            return license;
        }

        public async Task<bool> ActivateLicenseAsync(string orderNumber, string packId)
        {
            var result = await ValidateOrderAsync(orderNumber);
            if (result.IsValid && result.License != null)
            {
                _activeLicenses[packId] = result.License;
                await SaveLicensesAsync();
                return true;
            }
            return false;
        }

        public async Task<bool> IsPackLicensedAsync(string packId)
        {
            await LoadLicensesAsync();
            
            // Check for full license
            if (_activeLicenses.TryGetValue(packId, out var license))
            {
                return license.IsValid && (license.ExpiryDate == null || license.ExpiryDate > DateTime.Now);
            }

            // Check for trial license
            if (_trialLicenses.TryGetValue(packId, out var trial))
            {
                return trial.IsActive;
            }

            return false;
        }

        public async Task<TrialLicense> CreateTrialLicenseAsync(string packId, string email)
        {
            var trial = new TrialLicense
            {
                PackId = packId,
                Email = email,
                StartDate = DateTime.Now,
                ExpiryDate = DateTime.Now.AddDays(14), // 14-day trial
                FeaturesEnabled = GetPackFeatures(packId)
            };

            _trialLicenses[packId] = trial;
            await SaveTrialLicensesAsync();
            
            return trial;
        }

        public async Task<bool> IsTrialAvailableAsync(string packId, string email)
        {
            await LoadTrialLicensesAsync();
            
            // Check if trial already exists
            if (_trialLicenses.TryGetValue(packId, out var existingTrial))
            {
                return !existingTrial.IsActive; // Can create new trial if current one expired
            }

            return true; // No trial exists, so it's available
        }

        private Task<PackLicense?> CreateDemoLicenseAsync(string orderNumber)
        {
            // Demo order number patterns
            if (orderNumber.StartsWith("DEMO-", StringComparison.OrdinalIgnoreCase))
            {
                var packId = ExtractPackIdFromOrderNumber(orderNumber);
                
                return Task.FromResult<PackLicense?>(new PackLicense
                {
                    OrderNumber = orderNumber,
                    PackId = packId,
                    LicenseKey = GenerateLicenseKey(orderNumber),
                    CustomerEmail = "demo@westfall.software",
                    PurchaseDate = DateTime.Now,
                    ExpiryDate = null, // Lifetime for demo
                    LicenseType = LicenseType.Lifetime,
                    MaxInstallations = 3,
                    CurrentInstallations = 1,
                    IsValid = true,
                    FeaturesEnabled = GetPackFeatures(packId)
                });
            }

            // Trial order pattern
            if (orderNumber.StartsWith("TRIAL-", StringComparison.OrdinalIgnoreCase))
            {
                var packId = ExtractPackIdFromOrderNumber(orderNumber);
                
                return Task.FromResult<PackLicense?>(new PackLicense
                {
                    OrderNumber = orderNumber,
                    PackId = packId,
                    LicenseKey = GenerateLicenseKey(orderNumber),
                    CustomerEmail = "trial@westfall.software",
                    PurchaseDate = DateTime.Now,
                    ExpiryDate = DateTime.Now.AddDays(14),
                    LicenseType = LicenseType.Trial,
                    MaxInstallations = 1,
                    CurrentInstallations = 1,
                    IsValid = true,
                    FeaturesEnabled = GetPackFeatures(packId)
                });
            }

            return Task.FromResult<PackLicense?>(null);
        }

        private string ExtractPackIdFromOrderNumber(string orderNumber)
        {
            var parts = orderNumber.Split('-');
            if (parts.Length >= 2)
            {
                return parts[1].ToLower();
            }
            return "marketing-essentials"; // Default pack
        }

        private List<string> GetPackFeatures(string packId)
        {
            // Return features based on pack ID
            return packId switch
            {
                "marketing-essentials" => new List<string> 
                { 
                    "campaign-tracker", 
                    "social-media-manager", 
                    "lead-generator", 
                    "analytics-dashboard", 
                    "email-automation" 
                },
                "sales-pro" => new List<string> 
                { 
                    "crm-integration", 
                    "pipeline-management", 
                    "deal-tracking", 
                    "sales-analytics" 
                },
                "finance-manager" => new List<string> 
                { 
                    "expense-tracking", 
                    "invoice-generator", 
                    "financial-reports", 
                    "budget-planner" 
                },
                _ => new List<string> { "basic-features" }
            };
        }

        private string GenerateLicenseKey(string orderNumber)
        {
            using var sha256 = SHA256.Create();
            var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(orderNumber + DateTime.Now.ToString("yyyyMMdd")));
            return Convert.ToBase64String(hash)[..16]; // First 16 characters
        }

        private async Task LoadLicensesAsync()
        {
            try
            {
                var licensesFile = Path.Combine(_licensesPath, "licenses.json");
                if (_fileSystemService.FileExists(licensesFile))
                {
                    var json = await _fileSystemService.ReadAllTextAsync(licensesFile);
                    var licenses = JsonSerializer.Deserialize<Dictionary<string, PackLicense>>(json);
                    if (licenses != null)
                    {
                        _activeLicenses.Clear();
                        foreach (var kvp in licenses)
                        {
                            _activeLicenses[kvp.Key] = kvp.Value;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading licenses: {ex.Message}");
            }
        }

        private async Task SaveLicensesAsync()
        {
            try
            {
                var licensesFile = Path.Combine(_licensesPath, "licenses.json");
                var json = JsonSerializer.Serialize(_activeLicenses, new JsonSerializerOptions { WriteIndented = true });
                await _fileSystemService.WriteAllTextAsync(licensesFile, json);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving licenses: {ex.Message}");
            }
        }

        private async Task LoadTrialLicensesAsync()
        {
            try
            {
                var trialsFile = Path.Combine(_licensesPath, "trials.json");
                if (_fileSystemService.FileExists(trialsFile))
                {
                    var json = await _fileSystemService.ReadAllTextAsync(trialsFile);
                    var trials = JsonSerializer.Deserialize<Dictionary<string, TrialLicense>>(json);
                    if (trials != null)
                    {
                        _trialLicenses.Clear();
                        foreach (var kvp in trials)
                        {
                            _trialLicenses[kvp.Key] = kvp.Value;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading trial licenses: {ex.Message}");
            }
        }

        private async Task SaveTrialLicensesAsync()
        {
            try
            {
                var trialsFile = Path.Combine(_licensesPath, "trials.json");
                var json = JsonSerializer.Serialize(_trialLicenses, new JsonSerializerOptions { WriteIndented = true });
                await _fileSystemService.WriteAllTextAsync(trialsFile, json);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving trial licenses: {ex.Message}");
            }
        }
    }
}