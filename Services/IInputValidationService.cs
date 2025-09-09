using System;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using System.Linq;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for validating and sanitizing user input to prevent security vulnerabilities
    /// </summary>
    public interface IInputValidationService
    {
        // Input validation
        ValidationResult ValidateEmail(string email);
        ValidationResult ValidatePhoneNumber(string phoneNumber);
        ValidationResult ValidateText(string text, int maxLength = 1000);
        ValidationResult ValidateNumeric(string value, decimal? min = null, decimal? max = null);
        ValidationResult ValidateUrl(string url);
        ValidationResult ValidateFileName(string fileName);
        
        // Input sanitization
        string SanitizeHtml(string input);
        string SanitizeForDisplay(string input);
        string SanitizeFileName(string fileName);
        string SanitizePath(string path);
        
        // SQL injection protection
        string EscapeSqlParameter(string parameter);
        
        // XSS protection
        string PreventXss(string input);
        
        // File validation
        ValidationResult ValidateFileUpload(string fileName, byte[] content, string[] allowedExtensions, long maxSizeBytes);
    }
    
    public class ValidationResult
    {
        public bool IsValid { get; set; }
        public string ErrorMessage { get; set; }
        public List<string> Warnings { get; set; } = new List<string>();
        
        public static ValidationResult Success() => new ValidationResult { IsValid = true };
        public static ValidationResult Error(string message) => new ValidationResult { IsValid = false, ErrorMessage = message };
    }
}