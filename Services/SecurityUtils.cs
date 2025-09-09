using System;
using System.Security.Cryptography;
using System.Text;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for secure utility functions
    /// </summary>
    public interface ISecurityUtils
    {
        int GenerateSecureVerificationCode();
        string GenerateSecureToken(int lengthBytes = 32);
        byte[] GenerateSecureBytes(int length);
        string ComputeSecureHash(string input);
        bool VerifyHash(string input, string hash);
        string GenerateSecurePassword(int length = 16, bool includeSymbols = true);
        bool IsSecurePassword(string password);
    }

    /// <summary>
    /// Secure utilities for cryptographic operations and random generation
    /// </summary>
    public class SecurityUtils : ISecurityUtils
    {
        // Constants for secure operations
        private const int MinPasswordLength = 8;
        private const int MaxPasswordLength = 128;
        private const int DefaultTokenLength = 32;
        private const int VerificationCodeMin = 100000;
        private const int VerificationCodeMax = 999999;

        // Character sets for password generation
        private const string LowercaseChars = "abcdefghijklmnopqrstuvwxyz";
        private const string UppercaseChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        private const string DigitChars = "0123456789";
        private const string SymbolChars = "!@#$%^&*()_+-=[]{}|;:,.<>?";

        /// <summary>
        /// Generates a cryptographically secure 6-digit verification code
        /// Replaces insecure System.Random usage
        /// </summary>
        public int GenerateSecureVerificationCode()
        {
            try
            {
                using var rng = RandomNumberGenerator.Create();
                byte[] bytes = new byte[4];
                rng.GetBytes(bytes);
                
                // Convert to positive integer and ensure it's in valid range
                int value = Math.Abs(BitConverter.ToInt32(bytes, 0));
                int code = (value % (VerificationCodeMax - VerificationCodeMin + 1)) + VerificationCodeMin;
                
                Console.WriteLine("Secure verification code generated");
                return code;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to generate secure verification code: {ex.Message}");
                throw new InvalidOperationException("Failed to generate secure verification code", ex);
            }
        }

        /// <summary>
        /// Generates a cryptographically secure random token
        /// </summary>
        public string GenerateSecureToken(int lengthBytes = DefaultTokenLength)
        {
            if (lengthBytes <= 0 || lengthBytes > 256)
                throw new ArgumentException("Token length must be between 1 and 256 bytes", nameof(lengthBytes));

            try
            {
                var tokenBytes = GenerateSecureBytes(lengthBytes);
                var token = Convert.ToBase64String(tokenBytes);
                
                Console.WriteLine($"Secure token generated with length: {lengthBytes} bytes");
                return token;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to generate secure token with length: {lengthBytes}: {ex.Message}");
                throw new InvalidOperationException($"Failed to generate secure token with length: {lengthBytes}", ex);
            }
        }

        /// <summary>
        /// Generates cryptographically secure random bytes
        /// </summary>
        public byte[] GenerateSecureBytes(int length)
        {
            if (length <= 0)
                throw new ArgumentException("Length must be greater than zero", nameof(length));

            try
            {
                using var rng = RandomNumberGenerator.Create();
                byte[] bytes = new byte[length];
                rng.GetBytes(bytes);
                
                Console.WriteLine($"Secure bytes generated with length: {length}");
                return bytes;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to generate secure bytes with length: {length}: {ex.Message}");
                throw new InvalidOperationException($"Failed to generate secure bytes with length: {length}", ex);
            }
        }

        /// <summary>
        /// Computes a secure hash (SHA-256) of the input string
        /// </summary>
        public string ComputeSecureHash(string input)
        {
            if (string.IsNullOrEmpty(input))
                throw new ArgumentException("Input cannot be null or empty", nameof(input));

            try
            {
                using var sha256 = SHA256.Create();
                byte[] inputBytes = Encoding.UTF8.GetBytes(input);
                byte[] hashBytes = sha256.ComputeHash(inputBytes);
                
                var hash = Convert.ToBase64String(hashBytes);
                Console.WriteLine("Secure hash computed");
                return hash;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to compute secure hash: {ex.Message}");
                throw new InvalidOperationException("Failed to compute secure hash", ex);
            }
        }

        /// <summary>
        /// Verifies if an input string matches a given hash
        /// </summary>
        public bool VerifyHash(string input, string hash)
        {
            if (string.IsNullOrEmpty(input) || string.IsNullOrEmpty(hash))
                return false;

            try
            {
                var computedHash = ComputeSecureHash(input);
                bool isMatch = string.Equals(computedHash, hash, StringComparison.Ordinal);
                
                Console.WriteLine($"Hash verification completed: {(isMatch ? "MATCH" : "NO_MATCH")}");
                return isMatch;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to verify hash: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Generates a cryptographically secure password
        /// </summary>
        public string GenerateSecurePassword(int length = 16, bool includeSymbols = true)
        {
            if (length < MinPasswordLength || length > MaxPasswordLength)
                throw new ArgumentException($"Password length must be between {MinPasswordLength} and {MaxPasswordLength}", nameof(length));

            try
            {
                string characterSet = LowercaseChars + UppercaseChars + DigitChars;
                if (includeSymbols)
                    characterSet += SymbolChars;

                using var rng = RandomNumberGenerator.Create();
                var passwordBuilder = new StringBuilder(length);
                byte[] randomBytes = new byte[length * 4]; // Extra bytes for better distribution
                rng.GetBytes(randomBytes);

                // Ensure at least one character from each required set
                passwordBuilder.Append(GetRandomCharFromSet(LowercaseChars, randomBytes, 0));
                passwordBuilder.Append(GetRandomCharFromSet(UppercaseChars, randomBytes, 4));
                passwordBuilder.Append(GetRandomCharFromSet(DigitChars, randomBytes, 8));
                
                if (includeSymbols && length > 3)
                {
                    passwordBuilder.Append(GetRandomCharFromSet(SymbolChars, randomBytes, 12));
                }

                // Fill remaining characters
                int startIndex = includeSymbols && length > 3 ? 4 : 3;
                for (int i = startIndex; i < length; i++)
                {
                    int byteIndex = (i * 4) % randomBytes.Length;
                    int charIndex = Math.Abs(BitConverter.ToInt32(randomBytes, byteIndex)) % characterSet.Length;
                    passwordBuilder.Append(characterSet[charIndex]);
                }

                // Shuffle the password characters
                var password = ShuffleString(passwordBuilder.ToString(), randomBytes);
                
                Console.WriteLine($"Secure password generated with length: {length}, symbols: {includeSymbols}");
                return password;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to generate secure password with length: {length}: {ex.Message}");
                throw new InvalidOperationException($"Failed to generate secure password with length: {length}", ex);
            }
        }

        /// <summary>
        /// Validates if a password meets security requirements
        /// </summary>
        public bool IsSecurePassword(string password)
        {
            if (string.IsNullOrEmpty(password))
                return false;

            try
            {
                // Check minimum length
                if (password.Length < MinPasswordLength)
                    return false;

                // Check for required character types
                bool hasLowercase = false;
                bool hasUppercase = false;
                bool hasDigit = false;
                bool hasSymbol = false;

                foreach (char c in password)
                {
                    if (char.IsLower(c)) hasLowercase = true;
                    else if (char.IsUpper(c)) hasUppercase = true;
                    else if (char.IsDigit(c)) hasDigit = true;
                    else if (SymbolChars.Contains(c)) hasSymbol = true;
                }

                // Require at least 3 of 4 character types for passwords >= 8 chars
                int characterTypes = (hasLowercase ? 1 : 0) + (hasUppercase ? 1 : 0) + 
                                   (hasDigit ? 1 : 0) + (hasSymbol ? 1 : 0);

                bool isSecure = characterTypes >= 3;
                
                Console.WriteLine($"Password security validation: {(isSecure ? "SECURE" : "INSECURE")}");
                return isSecure;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Failed to validate password security: {ex.Message}");
                return false;
            }
        }

        private char GetRandomCharFromSet(string characterSet, byte[] randomBytes, int offset)
        {
            int value = Math.Abs(BitConverter.ToInt32(randomBytes, offset));
            int index = value % characterSet.Length;
            return characterSet[index];
        }

        private string ShuffleString(string input, byte[] randomBytes)
        {
            var chars = input.ToCharArray();
            
            for (int i = chars.Length - 1; i > 0; i--)
            {
                int byteIndex = (i * 4) % randomBytes.Length;
                int j = Math.Abs(BitConverter.ToInt32(randomBytes, byteIndex)) % (i + 1);
                
                // Swap characters
                (chars[i], chars[j]) = (chars[j], chars[i]);
            }
            
            return new string(chars);
        }
    }
}