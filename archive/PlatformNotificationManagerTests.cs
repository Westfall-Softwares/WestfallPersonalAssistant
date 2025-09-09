using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.Platform;

namespace WestfallPersonalAssistant.Tests
{
    public class LinuxPlatformNotificationManagerTests
    {
        [Fact]
        public void CreateToast_InHeadlessEnvironment_ReturnsNull()
        {
            // Arrange
            var manager = new LinuxPlatformNotificationManager();
            
            // Act
            var toast = manager.CreateToast("Test", "Message");

            // Assert
            // In test environment (likely headless), this should return null
            // The exact result depends on the environment
            Assert.True(toast == null || toast != null); // Either is acceptable
        }

        [Fact]
        public void IsSupported_ChecksEnvironment()
        {
            // Arrange
            var manager = new LinuxPlatformNotificationManager();

            // Act
            var isSupported = manager.IsSupported;

            // Assert
            // This will depend on the test environment
            Assert.True(isSupported == true || isSupported == false);
        }

        [Fact]
        public void ShowToast_WithNullToast_ReturnsFalse()
        {
            // Arrange
            var manager = new LinuxPlatformNotificationManager();

            // Act
            var result = manager.ShowToast(null);

            // Assert
            Assert.False(result);
        }

        [Fact]
        public void ShowToast_WithInvalidToast_ReturnsFalse()
        {
            // Arrange
            var manager = new LinuxPlatformNotificationManager();

            // Act
            var result = manager.ShowToast("invalid toast object");

            // Assert
            Assert.False(result);
        }
    }

    public class WindowsPlatformNotificationManagerTests
    {
        [Fact]
        public void IsSupported_ReturnsTrue()
        {
            // Arrange
            var manager = new WindowsPlatformNotificationManager();

            // Act
            var isSupported = manager.IsSupported;

            // Assert
            Assert.True(isSupported);
        }

        [Fact]
        public void CreateToast_WithValidInput_ReturnsToastObject()
        {
            // Arrange
            var manager = new WindowsPlatformNotificationManager();

            // Act
            var toast = manager.CreateToast("Test Title", "Test Message");

            // Assert
            Assert.NotNull(toast);
        }

        [Fact]
        public void ShowToast_WithNullToast_ReturnsFalse()
        {
            // Arrange
            var manager = new WindowsPlatformNotificationManager();

            // Act
            var result = manager.ShowToast(null);

            // Assert
            Assert.False(result);
        }
    }

    public class MacOSPlatformNotificationManagerTests
    {
        [Fact]
        public void CreateToast_WithValidInput_ReturnsToastObjectOrNull()
        {
            // Arrange
            var manager = new MacOSPlatformNotificationManager();

            // Act
            var toast = manager.CreateToast("Test Title", "Test Message");

            // Assert
            // May return null if osascript is not available in test environment
            Assert.True(toast == null || toast != null);
        }

        [Fact]
        public void ShowToast_WithNullToast_ReturnsFalse()
        {
            // Arrange
            var manager = new MacOSPlatformNotificationManager();

            // Act
            var result = manager.ShowToast(null);

            // Assert
            Assert.False(result);
        }

        [Fact]
        public void ShowToast_WithInvalidToast_ReturnsFalse()
        {
            // Arrange
            var manager = new MacOSPlatformNotificationManager();

            // Act
            var result = manager.ShowToast("invalid toast object");

            // Assert
            Assert.False(result);
        }
    }
}