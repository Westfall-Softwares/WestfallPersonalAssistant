using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Manager class that coordinates between different media player services
    /// and provides a unified interface for media playback
    /// </summary>
    public class MediaPlayerManager : IDisposable
    {
        private readonly Dictionary<MediaSourceType, IMediaPlayerService> _playerServices;
        private IMediaPlayerService? _activePlayer;
        private MediaSourceType _activeSourceType = MediaSourceType.Local;

        #region Events
        public event EventHandler<PlaybackStateChangedEventArgs>? PlaybackStateChanged;
        public event EventHandler<MediaItemChangedEventArgs>? MediaItemChanged;
        public event EventHandler<TimeSpan>? PositionChanged;
        #endregion

        #region Properties
        public PlaybackState State => _activePlayer?.State ?? PlaybackState.Stopped;
        public bool IsPlaying => _activePlayer?.IsPlaying ?? false;
        public MediaItem? CurrentItem => _activePlayer?.CurrentItem;
        public TimeSpan Position => _activePlayer?.Position ?? TimeSpan.Zero;
        public TimeSpan Duration => _activePlayer?.Duration ?? TimeSpan.Zero;
        
        public double Volume
        {
            get => _activePlayer?.Volume ?? 1.0;
            set
            {
                if (_activePlayer != null)
                    _activePlayer.Volume = value;
            }
        }
        
        public bool IsMuted
        {
            get => _activePlayer?.IsMuted ?? false;
            set
            {
                if (_activePlayer != null)
                    _activePlayer.IsMuted = value;
            }
        }
        
        public bool IsRepeatEnabled
        {
            get => _activePlayer?.IsRepeatEnabled ?? false;
            set
            {
                if (_activePlayer != null)
                    _activePlayer.IsRepeatEnabled = value;
            }
        }
        
        public bool IsShuffleEnabled
        {
            get => _activePlayer?.IsShuffleEnabled ?? false;
            set
            {
                if (_activePlayer != null)
                    _activePlayer.IsShuffleEnabled = value;
            }
        }

        public MediaSourceType ActiveSourceType => _activeSourceType;
        #endregion

        public MediaPlayerManager(
            IFileSystemService fileSystemService,
            ISecureStorageService secureStorageService,
            INetworkService networkService)
        {
            _playerServices = new Dictionary<MediaSourceType, IMediaPlayerService>
            {
                { MediaSourceType.Local, new LocalMediaPlayerService(fileSystemService) },
                { MediaSourceType.Spotify, new SpotifyMediaPlayerService(fileSystemService, secureStorageService) },
                { MediaSourceType.YouTube, new YouTubeMediaPlayerService(fileSystemService, networkService) }
            };

            // Subscribe to events from all player services
            foreach (var service in _playerServices.Values)
            {
                service.PlaybackStateChanged += OnPlayerStateChanged;
                service.MediaItemChanged += OnPlayerMediaItemChanged;
                service.PositionChanged += OnPlayerPositionChanged;
            }

            // Set local player as default active player
            _activePlayer = _playerServices[MediaSourceType.Local];
            _activeSourceType = MediaSourceType.Local;

            Console.WriteLine("MediaPlayerManager initialized with all player services");
        }

        /// <summary>
        /// Play a media item using the appropriate player service
        /// </summary>
        public async Task PlayAsync(MediaItem item)
        {
            if (item == null)
                throw new ArgumentNullException(nameof(item));

            // Switch to the appropriate player service if needed
            if (item.SourceType != _activeSourceType)
            {
                await SwitchPlayerServiceAsync(item.SourceType);
            }

            if (_activePlayer == null)
                throw new InvalidOperationException($"No player service available for source type: {item.SourceType}");

            await _activePlayer.PlayAsync(item);
        }

        /// <summary>
        /// Pause playback on the active player
        /// </summary>
        public async Task PauseAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.PauseAsync();
        }

        /// <summary>
        /// Resume playback on the active player
        /// </summary>
        public async Task ResumeAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.ResumeAsync();
        }

        /// <summary>
        /// Stop playback on the active player
        /// </summary>
        public async Task StopAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.StopAsync();
        }

        /// <summary>
        /// Skip to next track
        /// </summary>
        public async Task NextTrackAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.NextTrackAsync();
        }

        /// <summary>
        /// Skip to previous track
        /// </summary>
        public async Task PreviousTrackAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.PreviousTrackAsync();
        }

        /// <summary>
        /// Seek to a specific position
        /// </summary>
        public async Task SeekAsync(TimeSpan position)
        {
            if (_activePlayer != null)
                await _activePlayer.SeekAsync(position);
        }

        /// <summary>
        /// Set the playback queue
        /// </summary>
        public async Task SetQueueAsync(IEnumerable<MediaItem> items)
        {
            var itemsList = items.ToList();
            if (!itemsList.Any())
                return;

            // Group items by source type
            var groupedItems = itemsList.GroupBy(i => i.SourceType).ToList();

            if (groupedItems.Count == 1)
            {
                // All items are from the same source, use that player
                var sourceType = groupedItems.First().Key;
                await SwitchPlayerServiceAsync(sourceType);
                if (_activePlayer != null)
                    await _activePlayer.SetQueueAsync(itemsList);
            }
            else
            {
                // Mixed sources - for now, just use the first item's source type
                // In a more advanced implementation, you might want to handle cross-service playlists
                var firstSourceType = itemsList.First().SourceType;
                await SwitchPlayerServiceAsync(firstSourceType);
                
                // Filter items to only include those from the active source type
                var compatibleItems = itemsList.Where(i => i.SourceType == firstSourceType).ToList();
                if (_activePlayer != null && compatibleItems.Any())
                    await _activePlayer.SetQueueAsync(compatibleItems);
            }
        }

        /// <summary>
        /// Add item to the current queue
        /// </summary>
        public async Task AddToQueueAsync(MediaItem item)
        {
            if (item.SourceType != _activeSourceType)
            {
                // If it's a different source type, switch to that service
                await SwitchPlayerServiceAsync(item.SourceType);
            }

            if (_activePlayer != null)
                await _activePlayer.AddToQueueAsync(item);
        }

        /// <summary>
        /// Clear the current queue
        /// </summary>
        public async Task ClearQueueAsync()
        {
            if (_activePlayer != null)
                await _activePlayer.ClearQueueAsync();
        }

        /// <summary>
        /// Get recently played items from all services
        /// </summary>
        public async Task<List<MediaItem>> GetRecentlyPlayedAsync(int count = 10)
        {
            var allRecentItems = new List<MediaItem>();

            foreach (var service in _playerServices.Values)
            {
                try
                {
                    var recentItems = await service.GetRecentlyPlayedAsync(count);
                    allRecentItems.AddRange(recentItems);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error getting recently played items: {ex.Message}");
                }
            }

            // Sort by when they were actually played (would need to be tracked)
            // For now, just return the latest items up to the requested count
            return allRecentItems.TakeLast(count).ToList();
        }

        /// <summary>
        /// Get all playlists from all services
        /// </summary>
        public async Task<List<Playlist>> GetAllPlaylistsAsync()
        {
            var allPlaylists = new List<Playlist>();

            foreach (var service in _playerServices.Values)
            {
                try
                {
                    var playlists = await service.GetPlaylistsAsync();
                    allPlaylists.AddRange(playlists);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error getting playlists: {ex.Message}");
                }
            }

            return allPlaylists.OrderBy(p => p.Name).ToList();
        }

        /// <summary>
        /// Create a new playlist using the active player service
        /// </summary>
        public async Task<Playlist> CreatePlaylistAsync(string name)
        {
            if (_activePlayer == null)
                throw new InvalidOperationException("No active player service");

            return await _activePlayer.CreatePlaylistAsync(name);
        }

        /// <summary>
        /// Load a specific playlist
        /// </summary>
        public async Task<Playlist?> LoadPlaylistAsync(string id)
        {
            // Try to load from all services until found
            foreach (var service in _playerServices.Values)
            {
                try
                {
                    var playlist = await service.LoadPlaylistAsync(id);
                    if (playlist != null)
                        return playlist;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error loading playlist {id}: {ex.Message}");
                }
            }

            return null;
        }

        /// <summary>
        /// Save a playlist
        /// </summary>
        public async Task SavePlaylistAsync(Playlist playlist)
        {
            if (playlist.Items.Any())
            {
                // Determine which service to use based on the playlist items
                var sourceType = playlist.Items.First().SourceType;
                if (_playerServices.TryGetValue(sourceType, out var service))
                {
                    await service.SavePlaylistAsync(playlist);
                    return;
                }
            }

            // Fallback to active player
            if (_activePlayer != null)
                await _activePlayer.SavePlaylistAsync(playlist);
        }

        /// <summary>
        /// Get a specific player service
        /// </summary>
        public IMediaPlayerService? GetPlayerService(MediaSourceType sourceType)
        {
            return _playerServices.TryGetValue(sourceType, out var service) ? service : null;
        }

        /// <summary>
        /// Get the Spotify service for authentication
        /// </summary>
        public SpotifyMediaPlayerService? GetSpotifyService()
        {
            return GetPlayerService(MediaSourceType.Spotify) as SpotifyMediaPlayerService;
        }

        /// <summary>
        /// Get the YouTube service for searching
        /// </summary>
        public YouTubeMediaPlayerService? GetYouTubeService()
        {
            return GetPlayerService(MediaSourceType.YouTube) as YouTubeMediaPlayerService;
        }

        /// <summary>
        /// Switch to a different player service
        /// </summary>
        private async Task SwitchPlayerServiceAsync(MediaSourceType sourceType)
        {
            if (_activeSourceType == sourceType)
                return;

            // Stop current player if playing
            if (_activePlayer != null && _activePlayer.IsPlaying)
            {
                await _activePlayer.StopAsync();
            }

            // Switch to new player service
            if (_playerServices.TryGetValue(sourceType, out var newService))
            {
                _activePlayer = newService;
                _activeSourceType = sourceType;
                Console.WriteLine($"Switched to {sourceType} player service");
            }
            else
            {
                throw new NotSupportedException($"Player service for {sourceType} is not available");
            }
        }

        #region Event Handlers
        private void OnPlayerStateChanged(object? sender, PlaybackStateChangedEventArgs e)
        {
            if (sender == _activePlayer)
            {
                PlaybackStateChanged?.Invoke(this, e);
            }
        }

        private void OnPlayerMediaItemChanged(object? sender, MediaItemChangedEventArgs e)
        {
            if (sender == _activePlayer)
            {
                MediaItemChanged?.Invoke(this, e);
            }
        }

        private void OnPlayerPositionChanged(object? sender, TimeSpan e)
        {
            if (sender == _activePlayer)
            {
                PositionChanged?.Invoke(this, e);
            }
        }
        #endregion

        public void Dispose()
        {
            foreach (var service in _playerServices.Values)
            {
                service.PlaybackStateChanged -= OnPlayerStateChanged;
                service.MediaItemChanged -= OnPlayerMediaItemChanged;
                service.PositionChanged -= OnPlayerPositionChanged;
                service.Dispose();
            }

            _playerServices.Clear();
            _activePlayer = null;
            Console.WriteLine("MediaPlayerManager disposed");
        }
    }
}