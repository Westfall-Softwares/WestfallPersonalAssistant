using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Media source types supported by the player
    /// </summary>
    public enum MediaSourceType
    {
        Local,
        Spotify,
        YouTube,
        AppleMusic
    }

    /// <summary>
    /// Playback state of the media player
    /// </summary>
    public enum PlaybackState
    {
        Stopped,
        Playing,
        Paused,
        Buffering,
        Error
    }

    /// <summary>
    /// Represents a media item that can be played
    /// </summary>
    public class MediaItem
    {
        public string Id { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Artist { get; set; } = string.Empty;
        public string Album { get; set; } = string.Empty;
        public TimeSpan Duration { get; set; }
        public string ArtworkUrl { get; set; } = string.Empty;
        public MediaSourceType SourceType { get; set; }
        public string SourceSpecificData { get; set; } = string.Empty; // JSON for source-specific metadata
        public string FilePath { get; set; } = string.Empty; // For local files
    }

    /// <summary>
    /// Represents a playlist containing multiple media items
    /// </summary>
    public class Playlist
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public List<MediaItem> Items { get; set; } = new();
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
        public string Description { get; set; } = string.Empty;
        public bool IsDefault { get; set; }
    }

    /// <summary>
    /// Event arguments for playback state changes
    /// </summary>
    public class PlaybackStateChangedEventArgs : EventArgs
    {
        public PlaybackState OldState { get; }
        public PlaybackState NewState { get; }
        public string? ErrorMessage { get; }

        public PlaybackStateChangedEventArgs(PlaybackState oldState, PlaybackState newState, string? errorMessage = null)
        {
            OldState = oldState;
            NewState = newState;
            ErrorMessage = errorMessage;
        }
    }

    /// <summary>
    /// Event arguments for media item changes
    /// </summary>
    public class MediaItemChangedEventArgs : EventArgs
    {
        public MediaItem? PreviousItem { get; }
        public MediaItem? CurrentItem { get; }

        public MediaItemChangedEventArgs(MediaItem? previousItem, MediaItem? currentItem)
        {
            PreviousItem = previousItem;
            CurrentItem = currentItem;
        }
    }

    /// <summary>
    /// Core interface for media player services
    /// </summary>
    public interface IMediaPlayerService
    {
        #region Playback Control
        /// <summary>
        /// Play a specific media item
        /// </summary>
        Task PlayAsync(MediaItem item);

        /// <summary>
        /// Pause playback
        /// </summary>
        Task PauseAsync();

        /// <summary>
        /// Resume playback
        /// </summary>
        Task ResumeAsync();

        /// <summary>
        /// Stop playback
        /// </summary>
        Task StopAsync();

        /// <summary>
        /// Skip to next track
        /// </summary>
        Task NextTrackAsync();

        /// <summary>
        /// Skip to previous track
        /// </summary>
        Task PreviousTrackAsync();

        /// <summary>
        /// Seek to a specific position
        /// </summary>
        Task SeekAsync(TimeSpan position);
        #endregion

        #region State Properties
        /// <summary>
        /// Current playback state
        /// </summary>
        PlaybackState State { get; }

        /// <summary>
        /// Whether the player is currently playing
        /// </summary>
        bool IsPlaying { get; }

        /// <summary>
        /// Currently playing media item
        /// </summary>
        MediaItem? CurrentItem { get; }

        /// <summary>
        /// Current playback position
        /// </summary>
        TimeSpan Position { get; }

        /// <summary>
        /// Duration of current media item
        /// </summary>
        TimeSpan Duration { get; }

        /// <summary>
        /// Volume level (0.0 to 1.0)
        /// </summary>
        double Volume { get; set; }

        /// <summary>
        /// Whether audio is muted
        /// </summary>
        bool IsMuted { get; set; }

        /// <summary>
        /// Whether repeat mode is enabled
        /// </summary>
        bool IsRepeatEnabled { get; set; }

        /// <summary>
        /// Whether shuffle mode is enabled
        /// </summary>
        bool IsShuffleEnabled { get; set; }
        #endregion

        #region Events
        /// <summary>
        /// Fired when playback state changes
        /// </summary>
        event EventHandler<PlaybackStateChangedEventArgs>? PlaybackStateChanged;

        /// <summary>
        /// Fired when the current media item changes
        /// </summary>
        event EventHandler<MediaItemChangedEventArgs>? MediaItemChanged;

        /// <summary>
        /// Fired when playback position updates
        /// </summary>
        event EventHandler<TimeSpan>? PositionChanged;
        #endregion

        #region Playlist Management
        /// <summary>
        /// Create a new playlist
        /// </summary>
        Task<Playlist> CreatePlaylistAsync(string name);

        /// <summary>
        /// Load a playlist by ID
        /// </summary>
        Task<Playlist?> LoadPlaylistAsync(string id);

        /// <summary>
        /// Save a playlist
        /// </summary>
        Task SavePlaylistAsync(Playlist playlist);

        /// <summary>
        /// Delete a playlist
        /// </summary>
        Task DeletePlaylistAsync(string id);

        /// <summary>
        /// Get all available playlists
        /// </summary>
        Task<List<Playlist>> GetPlaylistsAsync();

        /// <summary>
        /// Set the current playing queue
        /// </summary>
        Task SetQueueAsync(IEnumerable<MediaItem> items);

        /// <summary>
        /// Add item to current queue
        /// </summary>
        Task AddToQueueAsync(MediaItem item);

        /// <summary>
        /// Clear the current queue
        /// </summary>
        Task ClearQueueAsync();
        #endregion

        #region Recently Played
        /// <summary>
        /// Get recently played items
        /// </summary>
        Task<List<MediaItem>> GetRecentlyPlayedAsync(int count = 10);

        /// <summary>
        /// Add item to recently played history
        /// </summary>
        Task AddToRecentlyPlayedAsync(MediaItem item);
        #endregion

        /// <summary>
        /// Dispose of resources
        /// </summary>
        void Dispose();
    }
}