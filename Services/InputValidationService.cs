using System;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text;
using System.Web;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Implementation of input validation and sanitization service
    /// </summary>
    public class InputValidationService : IInputValidationService
    {
        private static readonly Regex EmailRegex = new Regex(
            @"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            RegexOptions.Compiled | RegexOptions.IgnoreCase);
            
        private static readonly Regex PhoneRegex = new Regex(
            @"^\+?[1-9]\d{1,14}$|^(\(\d{3}\)\s?|\d{3}[-.]?)\d{3}[-.]?\d{4}$",
            RegexOptions.Compiled);
            
        private static readonly Regex UrlRegex = new Regex(
            @"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
            RegexOptions.Compiled | RegexOptions.IgnoreCase);
            
        private static readonly string[] DangerousFileExtensions = 
        {
            ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", ".jar", ".app", ".msi"
        };
        
        private static readonly char[] InvalidFileNameChars = Path.GetInvalidFileNameChars();
        private static readonly char[] InvalidPathChars = Path.GetInvalidPathChars();
        
        public ValidationResult ValidateEmail(string email)
        {
            if (string.IsNullOrWhiteSpace(email))
                return ValidationResult.Error("Email address is required");
                
            if (email.Length > 254)
                return ValidationResult.Error("Email address is too long");
                
            if (!EmailRegex.IsMatch(email))
                return ValidationResult.Error("Email address format is invalid");
                
            return ValidationResult.Success();
        }
        
        public ValidationResult ValidatePhoneNumber(string phoneNumber)
        {
            if (string.IsNullOrWhiteSpace(phoneNumber))
                return ValidationResult.Error("Phone number is required");
                
            var cleaned = Regex.Replace(phoneNumber, @"[\s\-\(\)\.]+", "");
            
            if (!PhoneRegex.IsMatch(cleaned))
                return ValidationResult.Error("Phone number format is invalid");
                
            return ValidationResult.Success();
        }
        
        public ValidationResult ValidateText(string text, int maxLength = 1000)
        {
            if (text == null)
                return ValidationResult.Success(); // null is allowed for optional fields
                
            if (text.Length > maxLength)
                return ValidationResult.Error($"Text length cannot exceed {maxLength} characters");
                
            // Check for potential script injection
            if (ContainsPotentialScript(text))
            {
                return ValidationResult.Error("Text contains potentially dangerous content");
            }
                
            return ValidationResult.Success();
        }
        
        public ValidationResult ValidateNumeric(string value, decimal? min = null, decimal? max = null)
        {
            if (string.IsNullOrWhiteSpace(value))
                return ValidationResult.Error("Numeric value is required");
                
            if (!decimal.TryParse(value, out decimal numericValue))
                return ValidationResult.Error("Value must be a valid number");
                
            if (min.HasValue && numericValue < min.Value)
                return ValidationResult.Error($"Value must be at least {min.Value}");
                
            if (max.HasValue && numericValue > max.Value)
                return ValidationResult.Error($"Value cannot exceed {max.Value}");
                
            return ValidationResult.Success();
        }
        
        public ValidationResult ValidateUrl(string url)
        {
            if (string.IsNullOrWhiteSpace(url))
                return ValidationResult.Error("URL is required");
                
            if (!UrlRegex.IsMatch(url))
                return ValidationResult.Error("URL format is invalid");
                
            // Additional security check
            if (url.Contains("javascript:") || url.Contains("data:") || url.Contains("vbscript:"))
                return ValidationResult.Error("URL contains potentially dangerous protocol");
                
            return ValidationResult.Success();
        }
        
        public ValidationResult ValidateFileName(string fileName)
        {
            if (string.IsNullOrWhiteSpace(fileName))
                return ValidationResult.Error("File name is required");
                
            if (fileName.IndexOfAny(InvalidFileNameChars) >= 0)
                return ValidationResult.Error("File name contains invalid characters");
                
            var extension = Path.GetExtension(fileName).ToLowerInvariant();
            if (DangerousFileExtensions.Contains(extension))
                return ValidationResult.Error("File type is not allowed for security reasons");
                
            if (fileName.Length > 255)
                return ValidationResult.Error("File name is too long");
                
            return ValidationResult.Success();
        }
        
        public string SanitizeHtml(string input)
        {
            if (string.IsNullOrEmpty(input))
                return string.Empty;
                
            // Basic HTML encoding to prevent XSS
            return HttpUtility.HtmlEncode(input);
        }
        
        public string SanitizeForDisplay(string input)
        {
            if (string.IsNullOrEmpty(input))
                return string.Empty;
                
            // Remove or encode potentially dangerous characters
            var sanitized = input
                .Replace("<", "&lt;")
                .Replace(">", "&gt;")
                .Replace("\"", "&quot;")
                .Replace("'", "&#x27;")
                .Replace("/", "&#x2F;");
                
            return sanitized;
        }
        
        public string SanitizeFileName(string fileName)
        {
            if (string.IsNullOrEmpty(fileName))
                return string.Empty;
                
            // Remove invalid characters
            foreach (var c in InvalidFileNameChars)
            {
                fileName = fileName.Replace(c, '_');
            }
            
            // Remove leading/trailing dots and spaces
            fileName = fileName.Trim(' ', '.');
            
            // Ensure it's not too long
            if (fileName.Length > 255)
                fileName = fileName.Substring(0, 255);
                
            return fileName;
        }
        
        public string SanitizePath(string path)
        {
            if (string.IsNullOrEmpty(path))
                return string.Empty;
                
            // Remove invalid characters
            foreach (var c in InvalidPathChars)
            {
                path = path.Replace(c, '_');
            }
            
            // Prevent directory traversal
            path = path.Replace("..", "");
            
            return path;
        }
        
        public string EscapeSqlParameter(string parameter)
        {
            if (string.IsNullOrEmpty(parameter))
                return string.Empty;
                
            // Basic SQL injection prevention (parameterized queries are preferred)
            return parameter.Replace("'", "''");
        }
        
        public string PreventXss(string input)
        {
            if (string.IsNullOrEmpty(input))
                return string.Empty;
                
            // Remove potentially dangerous patterns
            var patterns = new[]
            {
                @"<script[^>]*>.*?</script>",
                @"javascript:",
                @"vbscript:",
                @"onload=",
                @"onerror=",
                @"onclick=",
                @"onmouseover="
            };
            
            var result = input;
            foreach (var pattern in patterns)
            {
                result = Regex.Replace(result, pattern, "", RegexOptions.IgnoreCase);
            }
            
            return result;
        }
        
        public ValidationResult ValidateFileUpload(string fileName, byte[] content, string[] allowedExtensions, long maxSizeBytes)
        {
            var fileNameResult = ValidateFileName(fileName);
            if (!fileNameResult.IsValid)
                return fileNameResult;
                
            if (content == null || content.Length == 0)
                return ValidationResult.Error("File content is required");
                
            if (content.Length > maxSizeBytes)
                return ValidationResult.Error($"File size cannot exceed {maxSizeBytes / 1024 / 1024} MB");
                
            var extension = Path.GetExtension(fileName).ToLowerInvariant();
            if (allowedExtensions != null && !allowedExtensions.Contains(extension))
                return ValidationResult.Error($"File type '{extension}' is not allowed");
                
            // Basic file signature validation (magic numbers)
            if (!IsValidFileSignature(content, extension))
            {
                var result = ValidationResult.Success();
                result.Warnings.Add("File content may not match the file extension");
                return result;
            }
                
            return ValidationResult.Success();
        }
        
        private bool ContainsPotentialScript(string text)
        {
            var dangerousPatterns = new[]
            {
                "<script",
                "javascript:",
                "vbscript:",
                "data:text/html",
                "eval(",
                "expression("
            };
            
            return dangerousPatterns.Any(pattern => 
                text.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0);
        }
        
        private bool IsValidFileSignature(byte[] content, string extension)
        {
            if (content.Length < 4)
                return false;
                
            // Basic file signature validation
            var signatures = new Dictionary<string, byte[][]>
            {
                [".pdf"] = new[] { new byte[] { 0x25, 0x50, 0x44, 0x46 } },
                [".jpg"] = new[] { new byte[] { 0xFF, 0xD8, 0xFF } },
                [".jpeg"] = new[] { new byte[] { 0xFF, 0xD8, 0xFF } },
                [".png"] = new[] { new byte[] { 0x89, 0x50, 0x4E, 0x47 } },
                [".gif"] = new[] { new byte[] { 0x47, 0x49, 0x46, 0x38 } },
                [".zip"] = new[] { new byte[] { 0x50, 0x4B, 0x03, 0x04 } }
            };
            
            if (signatures.TryGetValue(extension, out var expectedSignatures))
            {
                return expectedSignatures.Any(signature => 
                    content.Take(signature.Length).SequenceEqual(signature));
            }
            
            // If we don't have a signature to check, allow it
            return true;
        }
    }
}