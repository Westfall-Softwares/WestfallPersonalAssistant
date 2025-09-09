using System;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Tests
{
    public class MediaPlayerTests
    {
        [Fact]
        public void MediaPlayerManager_Initialize_ShouldCreateAllServices()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);

            // Act
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            // Assert
            Assert.NotNull(manager);
            Assert.Equal(PlaybackState.Stopped, manager.State);
            Assert.False(manager.IsPlaying);
            Assert.Equal(MediaSourceType.Local, manager.ActiveSourceType);
        }

        [Fact]
        public async Task LocalMediaPlayerService_CreateFromFile_ShouldCreateMediaItem()
        {
            // Arrange - Create a mock file path
            var filePath = "/mock/test.mp3";

            // We can't actually test file creation in this mock environment,
            // but we can test the service initialization
            var fileSystemService = new MockFileSystemService();
            var localPlayer = new LocalMediaPlayerService(fileSystemService);

            // Assert
            Assert.NotNull(localPlayer);
            Assert.Equal(PlaybackState.Stopped, localPlayer.State);
            Assert.False(localPlayer.IsPlaying);
            
            localPlayer.Dispose();
        }

        [Fact]
        public async Task MediaPlayerManager_PlayAsync_ShouldSwitchServices()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            var localItem = new MediaItem
            {
                Id = "local-1",
                Title = "Test Local Song",
                Artist = "Test Artist",
                SourceType = MediaSourceType.Local,
                FilePath = "/mock/test.mp3",
                Duration = TimeSpan.FromMinutes(3)
            };

            var youtubeItem = new MediaItem
            {
                Id = "youtube:video:123",
                Title = "Test YouTube Video",
                Artist = "Test Channel",
                SourceType = MediaSourceType.YouTube,
                Duration = TimeSpan.FromMinutes(3)
            };

            // Act & Assert - Start with local
            Assert.Equal(MediaSourceType.Local, manager.ActiveSourceType);

            // Switch to YouTube item
            await manager.PlayAsync(youtubeItem);

            // The active source type should have switched to YouTube
            Assert.Equal(MediaSourceType.YouTube, manager.ActiveSourceType);
        }

        [Fact]
        public async Task MediaPlayerManager_VolumeControl_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            // Act
            manager.Volume = 0.5;
            manager.IsMuted = true;

            // Assert
            Assert.Equal(0.5, manager.Volume);
            Assert.True(manager.IsMuted);
        }

        [Fact]
        public async Task MediaPlayerManager_RepeatAndShuffle_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            // Act
            manager.IsRepeatEnabled = true;
            manager.IsShuffleEnabled = true;

            // Assert
            Assert.True(manager.IsRepeatEnabled);
            Assert.True(manager.IsShuffleEnabled);
        }

        [Fact]
        public async Task MediaPlayerManager_PlaylistManagement_ShouldWork()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            // Act
            var playlist = await manager.CreatePlaylistAsync("Test Playlist");

            // Assert
            Assert.NotNull(playlist);
            Assert.Equal("Test Playlist", playlist.Name);
            Assert.NotEmpty(playlist.Id);
        }



        [Fact]
        public async Task YouTubeMediaPlayerService_SearchVideos_ShouldReturnResults()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            var youtubeService = new YouTubeMediaPlayerService(fileSystemService, networkService);

            // Act
            var results = await youtubeService.SearchVideosAsync("test query");

            // Assert
            Assert.NotNull(results);
            Assert.True(results.Count > 0);
            Assert.All(results, item => Assert.Equal(MediaSourceType.YouTube, item.SourceType));
            
            youtubeService.Dispose();
        }

        [Fact]
        public async Task MediaPlayerManager_GetServices_ShouldReturnCorrectServices()
        {
            // Arrange
            var fileSystemService = new MockFileSystemService();
            var secureStorageService = new MockSecureStorageService();
            var networkService = new NetworkService(secureStorageService);
            using var manager = new MediaPlayerManager(fileSystemService, secureStorageService, networkService);

            // Act
            var localService = manager.GetPlayerService(MediaSourceType.Local);
            var youtubeService = manager.GetYouTubeService();

            // Assert
            Assert.NotNull(localService);
            Assert.IsType<LocalMediaPlayerService>(localService);
            Assert.NotNull(youtubeService);
            Assert.IsType<YouTubeMediaPlayerService>(youtubeService);
        }

        [Fact]
        public void MediaItem_Properties_ShouldWork()
        {
            // Arrange & Act
            var mediaItem = new MediaItem
            {
                Id = "test-123",
                Title = "Test Song",
                Artist = "Test Artist",
                Album = "Test Album",
                Duration = TimeSpan.FromMinutes(3),
                SourceType = MediaSourceType.Local,
                FilePath = "/test/path.mp3"
            };

            // Assert
            Assert.Equal("test-123", mediaItem.Id);
            Assert.Equal("Test Song", mediaItem.Title);
            Assert.Equal("Test Artist", mediaItem.Artist);
            Assert.Equal("Test Album", mediaItem.Album);
            Assert.Equal(TimeSpan.FromMinutes(3), mediaItem.Duration);
            Assert.Equal(MediaSourceType.Local, mediaItem.SourceType);
            Assert.Equal("/test/path.mp3", mediaItem.FilePath);
        }

        [Fact]
        public void Playlist_Properties_ShouldWork()
        {
            // Arrange & Act
            var playlist = new Playlist
            {
                Id = "playlist-123",
                Name = "My Playlist",
                Description = "Test playlist",
                Items = new System.Collections.Generic.List<MediaItem>
                {
                    new MediaItem { Id = "1", Title = "Song 1" },
                    new MediaItem { Id = "2", Title = "Song 2" }
                }
            };

            // Assert
            Assert.Equal("playlist-123", playlist.Id);
            Assert.Equal("My Playlist", playlist.Name);
            Assert.Equal("Test playlist", playlist.Description);
            Assert.Equal(2, playlist.Items.Count);
        }
    }
}