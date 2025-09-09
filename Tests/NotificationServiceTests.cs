using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;
using WestfallPersonalAssistant.Platform;

namespace WestfallPersonalAssistant.Tests
{
    public class NotificationServiceTests
    {
        private class MockPlatformNotificationManager : IPlatformNotificationManager
        {
            public bool IsSupported { get; set; } = true;
            public bool ShouldReturnNull { get; set; } = false;

            public object? CreateToast(string title, string message)
            {
                return ShouldReturnNull ? null : new { Title = title, Message = message };
            }

            public bool ShowToast(object toast)
            {
                return toast != null;
            }
        }

        private class MockPlatformService : IPlatformService
        {
            public string GetPlatformName() => "Test";
            public string GetAppDataPath() => "/test";
            public void ShowNotification(string title, string message) { }
            public bool IsElevated() => false;
            public bool SupportsNativeNotifications() => true;
            public bool SupportsFileSystemFeatures() => true;
            public PlatformCapabilities GetCapabilities() => new PlatformCapabilities();
        }

        [Fact]
        public async Task ShowToastAsync_WithSupportedPlatform_ReturnsTrue()
        {
            // Arrange
            var platformManager = new MockPlatformNotificationManager { IsSupported = true };
            var platformService = new MockPlatformService();
            var notificationService = new NotificationService(platformManager, platformService);

            // Act
            var result = await notificationService.ShowToastAsync("Test Title", "Test Message");

            // Assert
            Assert.True(result);
        }

        [Fact]
        public async Task ShowToastAsync_WithNullToast_ReturnsFalseAndDoesNotThrow()
        {
            // Arrange
            var platformManager = new MockPlatformNotificationManager 
            { 
                IsSupported = true, 
                ShouldReturnNull = true 
            };
            var platformService = new MockPlatformService();
            var notificationService = new NotificationService(platformManager, platformService);

            // Act
            var result = await notificationService.ShowToastAsync("Test Title", "Test Message");

            // Assert
            Assert.False(result); // Should return false when CreateToast returns null
        }

        [Fact]
        public async Task ShowToastAsync_WithUnsupportedPlatform_ReturnsFalse()
        {
            // Arrange
            var platformManager = new MockPlatformNotificationManager { IsSupported = false };
            var platformService = new MockPlatformService();
            var notificationService = new NotificationService(platformManager, platformService);

            // Act
            var result = await notificationService.ShowToastAsync("Test Title", "Test Message");

            // Assert
            Assert.False(result);
        }

        [Fact]
        public async Task ShowNotificationAsync_WithToastFailure_FallsBackToPlatformService()
        {
            // Arrange
            var platformManager = new MockPlatformNotificationManager 
            { 
                IsSupported = true, 
                ShouldReturnNull = true 
            };
            var platformService = new MockPlatformService();
            var notificationService = new NotificationService(platformManager, platformService);

            // Act
            var result = await notificationService.ShowNotificationAsync("Test Title", "Test Message");

            // Assert
            Assert.True(result); // Should fallback to platform service and succeed
        }

        [Fact]
        public void IsToastSupported_WithSupportedPlatform_ReturnsTrue()
        {
            // Arrange
            var platformManager = new MockPlatformNotificationManager { IsSupported = true };
            var platformService = new MockPlatformService();
            var notificationService = new NotificationService(platformManager, platformService);

            // Act
            var result = notificationService.IsToastSupported();

            // Assert
            Assert.True(result);
        }

        [Fact]
        public void Constructor_WithNullPlatformNotificationManager_ThrowsArgumentNullException()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentNullException>(() => 
                new NotificationService(null, new MockPlatformService()));
        }

        [Fact]
        public void Constructor_WithNullPlatformService_ThrowsArgumentNullException()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentNullException>(() => 
                new NotificationService(new MockPlatformNotificationManager(), null));
        }
    }
}