using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    public interface IOrderVerificationService
    {
        Task<OrderValidationResult> ValidateOrderAsync(string orderNumber);
        Task<PackLicense?> GetLicenseAsync(string packId);
        Task<bool> ActivateLicenseAsync(string orderNumber, string packId);
        Task<bool> IsPackLicensedAsync(string packId);
        Task<TrialLicense> CreateTrialLicenseAsync(string packId, string email);
        Task<bool> IsTrialAvailableAsync(string packId, string email);
    }

    public class OrderValidationResult
    {
        public bool IsValid { get; set; }
        public string? ErrorMessage { get; set; }
        public PackLicense? License { get; set; }
        public bool TrialAvailable { get; set; }
    }

    public class PackLicense
    {
        public string OrderNumber { get; set; } = string.Empty;
        public string PackId { get; set; } = string.Empty;
        public string LicenseKey { get; set; } = string.Empty;
        public string CustomerEmail { get; set; } = string.Empty;
        public DateTime PurchaseDate { get; set; }
        public DateTime? ExpiryDate { get; set; }
        public LicenseType LicenseType { get; set; }
        public int MaxInstallations { get; set; }
        public int CurrentInstallations { get; set; }
        public bool IsValid { get; set; }
        public List<string> FeaturesEnabled { get; set; } = new();
    }

    public class TrialLicense
    {
        public string PackId { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public DateTime StartDate { get; set; }
        public DateTime ExpiryDate { get; set; }
        public List<string> FeaturesEnabled { get; set; } = new();
        public bool IsActive => DateTime.Now <= ExpiryDate;
    }

    public enum LicenseType
    {
        Trial,
        Monthly,
        Yearly,
        Lifetime
    }
}