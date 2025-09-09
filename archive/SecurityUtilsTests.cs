using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Tests
{
    public class SecurityUtilsTests
    {
        private readonly SecurityUtils _securityUtils;

        public SecurityUtilsTests()
        {
            _securityUtils = new SecurityUtils();
        }

        [Fact]
        public void GenerateSecureVerificationCode_ShouldReturnSixDigitCode()
        {
            // Act
            var code = _securityUtils.GenerateSecureVerificationCode();

            // Assert
            Assert.True(code >= 100000 && code <= 999999, $"Code {code} should be a 6-digit number");
        }

        [Fact]
        public void GenerateSecureVerificationCode_ShouldReturnDifferentCodesOnMultipleCalls()
        {
            // Act
            var code1 = _securityUtils.GenerateSecureVerificationCode();
            var code2 = _securityUtils.GenerateSecureVerificationCode();
            var code3 = _securityUtils.GenerateSecureVerificationCode();

            // Assert
            Assert.NotEqual(code1, code2);
            Assert.NotEqual(code2, code3);
            Assert.NotEqual(code1, code3);
        }

        [Fact]
        public void GenerateSecureToken_WithDefaultLength_ShouldReturnBase64Token()
        {
            // Act
            var token = _securityUtils.GenerateSecureToken();

            // Assert
            Assert.NotNull(token);
            Assert.NotEmpty(token);
            
            // Should be valid base64
            var bytes = Convert.FromBase64String(token);
            Assert.Equal(32, bytes.Length); // Default length
        }

        [Theory]
        [InlineData(16)]
        [InlineData(32)]
        [InlineData(64)]
        public void GenerateSecureToken_WithSpecificLength_ShouldReturnCorrectLength(int length)
        {
            // Act
            var token = _securityUtils.GenerateSecureToken(length);

            // Assert
            var bytes = Convert.FromBase64String(token);
            Assert.Equal(length, bytes.Length);
        }

        [Theory]
        [InlineData(0)]
        [InlineData(-1)]
        [InlineData(257)]
        public void GenerateSecureToken_WithInvalidLength_ShouldThrowArgumentException(int invalidLength)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _securityUtils.GenerateSecureToken(invalidLength));
        }

        [Fact]
        public void GenerateSecureBytes_ShouldReturnCorrectLength()
        {
            // Arrange
            const int expectedLength = 64;

            // Act
            var bytes = _securityUtils.GenerateSecureBytes(expectedLength);

            // Assert
            Assert.Equal(expectedLength, bytes.Length);
        }

        [Fact]
        public void GenerateSecureBytes_ShouldReturnDifferentArraysOnMultipleCalls()
        {
            // Act
            var bytes1 = _securityUtils.GenerateSecureBytes(32);
            var bytes2 = _securityUtils.GenerateSecureBytes(32);

            // Assert
            Assert.NotEqual(bytes1, bytes2);
        }

        [Theory]
        [InlineData(0)]
        [InlineData(-1)]
        public void GenerateSecureBytes_WithInvalidLength_ShouldThrowArgumentException(int invalidLength)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _securityUtils.GenerateSecureBytes(invalidLength));
        }

        [Fact]
        public void ComputeSecureHash_ShouldReturnConsistentHash()
        {
            // Arrange
            const string input = "test string for hashing";

            // Act
            var hash1 = _securityUtils.ComputeSecureHash(input);
            var hash2 = _securityUtils.ComputeSecureHash(input);

            // Assert
            Assert.Equal(hash1, hash2);
            Assert.NotNull(hash1);
            Assert.NotEmpty(hash1);
        }

        [Fact]
        public void ComputeSecureHash_WithDifferentInputs_ShouldReturnDifferentHashes()
        {
            // Act
            var hash1 = _securityUtils.ComputeSecureHash("input1");
            var hash2 = _securityUtils.ComputeSecureHash("input2");

            // Assert
            Assert.NotEqual(hash1, hash2);
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        public void ComputeSecureHash_WithNullOrEmptyInput_ShouldThrowArgumentException(string input)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _securityUtils.ComputeSecureHash(input));
        }

        [Fact]
        public void VerifyHash_WithMatchingInputAndHash_ShouldReturnTrue()
        {
            // Arrange
            const string input = "test input";
            var hash = _securityUtils.ComputeSecureHash(input);

            // Act
            var result = _securityUtils.VerifyHash(input, hash);

            // Assert
            Assert.True(result);
        }

        [Fact]
        public void VerifyHash_WithNonMatchingInputAndHash_ShouldReturnFalse()
        {
            // Arrange
            const string input = "test input";
            const string wrongInput = "wrong input";
            var hash = _securityUtils.ComputeSecureHash(input);

            // Act
            var result = _securityUtils.VerifyHash(wrongInput, hash);

            // Assert
            Assert.False(result);
        }

        [Theory]
        [InlineData(null, "hash")]
        [InlineData("", "hash")]
        [InlineData("input", null)]
        [InlineData("input", "")]
        public void VerifyHash_WithNullOrEmptyInputs_ShouldReturnFalse(string input, string hash)
        {
            // Act
            var result = _securityUtils.VerifyHash(input, hash);

            // Assert
            Assert.False(result);
        }

        [Theory]
        [InlineData(8, true)]
        [InlineData(16, true)]
        [InlineData(32, false)]
        public void GenerateSecurePassword_ShouldReturnPasswordOfCorrectLength(int length, bool includeSymbols)
        {
            // Act
            var password = _securityUtils.GenerateSecurePassword(length, includeSymbols);

            // Assert
            Assert.Equal(length, password.Length);
        }

        [Fact]
        public void GenerateSecurePassword_ShouldReturnDifferentPasswordsOnMultipleCalls()
        {
            // Act
            var password1 = _securityUtils.GenerateSecurePassword();
            var password2 = _securityUtils.GenerateSecurePassword();
            var password3 = _securityUtils.GenerateSecurePassword();

            // Assert
            Assert.NotEqual(password1, password2);
            Assert.NotEqual(password2, password3);
            Assert.NotEqual(password1, password3);
        }

        [Theory]
        [InlineData(7)]
        [InlineData(129)]
        public void GenerateSecurePassword_WithInvalidLength_ShouldThrowArgumentException(int invalidLength)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => _securityUtils.GenerateSecurePassword(invalidLength));
        }

        [Theory]
        [InlineData("Password123!", true)]
        [InlineData("password123!", true)] // Has lowercase, digits, symbols (3/4 types)
        [InlineData("PASSWORD123!", true)] // Has uppercase, digits, symbols (3/4 types) 
        [InlineData("Password!", true)]    // Has uppercase, lowercase, symbols (3/4 types)
        [InlineData("Password123", true)]  // Has uppercase, lowercase, digits (3/4 types)
        [InlineData("Pass1!", false)]       // Too short
        [InlineData("password", false)]     // Only lowercase (1/4 types)
        [InlineData("", false)]             // Empty
        [InlineData(null, false)]           // Null
        public void IsSecurePassword_ShouldValidatePasswordCorrectly(string password, bool expectedResult)
        {
            // Act
            var result = _securityUtils.IsSecurePassword(password);

            // Assert
            Assert.Equal(expectedResult, result);
        }

        [Fact]
        public void IsSecurePassword_WithGeneratedPassword_ShouldReturnTrue()
        {
            // Act
            var password = _securityUtils.GenerateSecurePassword(16, true);
            var isSecure = _securityUtils.IsSecurePassword(password);

            // Assert
            Assert.True(isSecure, $"Generated password '{password}' should be secure");
        }
    }
}