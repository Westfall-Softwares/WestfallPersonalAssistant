using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Timers;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Base implementation of media player service
    /// </summary>
    public abstract class BaseMediaPlayerService : IMediaPlayerService, IDisposable
    {
        protected readonly IFileSystemService _fileSystemService;
        protected readonly System.Timers.Timer _positionTimer;
        protected readonly List<MediaItem> _queue = new();
        protected readonly List<MediaItem> _recentlyPlayed = new();
        protected int _currentQueueIndex = -1;
        protected PlaybackState _state = PlaybackState.Stopped;
        protected MediaItem? _currentItem;
        protected TimeSpan _position = TimeSpan.Zero;
        protected double _volume = 1.0;
        protected bool _isMuted = false;
        protected bool _isRepeatEnabled = false;
        protected bool _isShuffleEnabled = false;

        #region Events
        public event EventHandler<PlaybackStateChangedEventArgs>? PlaybackStateChanged;
        public event EventHandler<MediaItemChangedEventArgs>? MediaItemChanged;
        public event EventHandler<TimeSpan>? PositionChanged;
        #endregion

        #region Properties
        public PlaybackState State => _state;
        public bool IsPlaying => _state == PlaybackState.Playing;
        public MediaItem? CurrentItem => _currentItem;
        public TimeSpan Position => _position;
        public abstract TimeSpan Duration { get; }
        
        public double Volume
        {
            get => _volume;
            set
            {
                _volume = Math.Max(0.0, Math.Min(1.0, value));
                OnVolumeChanged(_volume);
            }
        }
        
        public bool IsMuted
        {
            get => _isMuted;
            set
            {
                _isMuted = value;
                OnMuteChanged(_isMuted);
            }
        }
        
        public bool IsRepeatEnabled
        {
            get => _isRepeatEnabled;
            set => _isRepeatEnabled = value;
        }
        
        public bool IsShuffleEnabled
        {
            get => _isShuffleEnabled;
            set => _isShuffleEnabled = value;
        }
        #endregion

        protected BaseMediaPlayerService(IFileSystemService fileSystemService)
        {
            _fileSystemService = fileSystemService ?? throw new ArgumentNullException(nameof(fileSystemService));
            
            // Set up position timer
            _positionTimer = new System.Timers.Timer(1000); // Update every second
            _positionTimer.Elapsed += OnPositionTimerElapsed;
        }

        #region Abstract Methods
        protected abstract Task PlayInternalAsync(MediaItem item);
        protected abstract Task PauseInternalAsync();
        protected abstract Task ResumeInternalAsync();
        protected abstract Task StopInternalAsync();
        protected abstract Task SeekInternalAsync(TimeSpan position);
        protected abstract void OnVolumeChanged(double volume);
        protected abstract void OnMuteChanged(bool isMuted);
        protected abstract TimeSpan GetCurrentPosition();
        #endregion

        #region Public Methods
        public virtual async Task PlayAsync(MediaItem item)
        {
            if (item == null)
                throw new ArgumentNullException(nameof(item));

            var previousItem = _currentItem;
            _currentItem = item;

            try
            {
                await PlayInternalAsync(item);
                await AddToRecentlyPlayedAsync(item);
                
                SetState(PlaybackState.Playing);
                OnMediaItemChanged(previousItem, _currentItem);
                _positionTimer.Start();
            }
            catch (Exception ex)
            {
                SetState(PlaybackState.Error, ex.Message);
                throw;
            }
        }

        public virtual async Task PauseAsync()
        {
            if (_state != PlaybackState.Playing)
                return;

            try
            {
                await PauseInternalAsync();
                SetState(PlaybackState.Paused);
                _positionTimer.Stop();
            }
            catch (Exception ex)
            {
                SetState(PlaybackState.Error, ex.Message);
                throw;
            }
        }

        public virtual async Task ResumeAsync()
        {
            if (_state != PlaybackState.Paused)
                return;

            try
            {
                await ResumeInternalAsync();
                SetState(PlaybackState.Playing);
                _positionTimer.Start();
            }
            catch (Exception ex)
            {
                SetState(PlaybackState.Error, ex.Message);
                throw;
            }
        }

        public virtual async Task StopAsync()
        {
            try
            {
                await StopInternalAsync();
                SetState(PlaybackState.Stopped);
                _positionTimer.Stop();
                _position = TimeSpan.Zero;
                OnPositionChanged(_position);
            }
            catch (Exception ex)
            {
                SetState(PlaybackState.Error, ex.Message);
                throw;
            }
        }

        public virtual async Task NextTrackAsync()
        {
            if (_queue.Count == 0 || _currentQueueIndex < 0)
                return;

            int nextIndex;
            if (_isShuffleEnabled)
            {
                var random = new Random();
                nextIndex = random.Next(_queue.Count);
            }
            else
            {
                nextIndex = _currentQueueIndex + 1;
                if (nextIndex >= _queue.Count)
                {
                    if (_isRepeatEnabled)
                        nextIndex = 0;
                    else
                        return; // End of queue
                }
            }

            _currentQueueIndex = nextIndex;
            await PlayAsync(_queue[_currentQueueIndex]);
        }

        public virtual async Task PreviousTrackAsync()
        {
            if (_queue.Count == 0 || _currentQueueIndex < 0)
                return;

            int prevIndex;
            if (_isShuffleEnabled)
            {
                var random = new Random();
                prevIndex = random.Next(_queue.Count);
            }
            else
            {
                prevIndex = _currentQueueIndex - 1;
                if (prevIndex < 0)
                {
                    if (_isRepeatEnabled)
                        prevIndex = _queue.Count - 1;
                    else
                        return; // Beginning of queue
                }
            }

            _currentQueueIndex = prevIndex;
            await PlayAsync(_queue[_currentQueueIndex]);
        }

        public virtual async Task SeekAsync(TimeSpan position)
        {
            if (_currentItem == null || position < TimeSpan.Zero)
                return;

            try
            {
                await SeekInternalAsync(position);
                _position = position;
                OnPositionChanged(_position);
            }
            catch (Exception ex)
            {
                SetState(PlaybackState.Error, ex.Message);
                throw;
            }
        }
        #endregion

        #region Playlist Management
        public virtual async Task<Playlist> CreatePlaylistAsync(string name)
        {
            var playlist = new Playlist
            {
                Id = Guid.NewGuid().ToString(),
                Name = name,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };

            await SavePlaylistAsync(playlist);
            return playlist;
        }

        public virtual async Task<Playlist?> LoadPlaylistAsync(string id)
        {
            try
            {
                var playlistsPath = Path.Combine(_fileSystemService.GetAppDataPath(), "Playlists");
                var playlistFile = Path.Combine(playlistsPath, $"{id}.json");

                if (!_fileSystemService.FileExists(playlistFile))
                    return null;

                var json = await _fileSystemService.ReadAllTextAsync(playlistFile);
                return JsonSerializer.Deserialize<Playlist>(json);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading playlist {id}: {ex.Message}");
                return null;
            }
        }

        public virtual async Task SavePlaylistAsync(Playlist playlist)
        {
            try
            {
                var playlistsPath = Path.Combine(_fileSystemService.GetAppDataPath(), "Playlists");
                if (!_fileSystemService.DirectoryExists(playlistsPath))
                    _fileSystemService.CreateDirectory(playlistsPath);

                playlist.UpdatedAt = DateTime.UtcNow;
                var playlistFile = Path.Combine(playlistsPath, $"{playlist.Id}.json");
                var json = JsonSerializer.Serialize(playlist, new JsonSerializerOptions { WriteIndented = true });
                
                await _fileSystemService.WriteAllTextAsync(playlistFile, json);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving playlist {playlist.Name}: {ex.Message}");
                throw;
            }
        }

        public virtual async Task DeletePlaylistAsync(string id)
        {
            try
            {
                var playlistsPath = Path.Combine(_fileSystemService.GetAppDataPath(), "Playlists");
                var playlistFile = Path.Combine(playlistsPath, $"{id}.json");

                if (_fileSystemService.FileExists(playlistFile))
                {
                    File.Delete(playlistFile);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error deleting playlist {id}: {ex.Message}");
                throw;
            }
        }

        public virtual async Task<List<Playlist>> GetPlaylistsAsync()
        {
            try
            {
                var playlists = new List<Playlist>();
                var playlistsPath = Path.Combine(_fileSystemService.GetAppDataPath(), "Playlists");

                if (!_fileSystemService.DirectoryExists(playlistsPath))
                    return playlists;

                var playlistFiles = _fileSystemService.GetFiles(playlistsPath, "*.json");

                foreach (var file in playlistFiles)
                {
                    try
                    {
                        var json = await _fileSystemService.ReadAllTextAsync(file);
                        var playlist = JsonSerializer.Deserialize<Playlist>(json);
                        if (playlist != null)
                            playlists.Add(playlist);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error loading playlist file {file}: {ex.Message}");
                    }
                }

                return playlists.OrderBy(p => p.Name).ToList();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting playlists: {ex.Message}");
                return new List<Playlist>();
            }
        }

        public virtual async Task SetQueueAsync(IEnumerable<MediaItem> items)
        {
            _queue.Clear();
            _queue.AddRange(items);
            _currentQueueIndex = _queue.Count > 0 ? 0 : -1;
            
            if (_currentQueueIndex >= 0)
                await PlayAsync(_queue[_currentQueueIndex]);
        }

        public virtual async Task AddToQueueAsync(MediaItem item)
        {
            _queue.Add(item);
            if (_currentQueueIndex < 0)
            {
                _currentQueueIndex = 0;
                await PlayAsync(item);
            }
        }

        public virtual Task ClearQueueAsync()
        {
            _queue.Clear();
            _currentQueueIndex = -1;
            return Task.CompletedTask;
        }
        #endregion

        #region Recently Played
        public virtual Task<List<MediaItem>> GetRecentlyPlayedAsync(int count = 10)
        {
            return Task.FromResult(_recentlyPlayed.TakeLast(count).Reverse().ToList());
        }

        public virtual Task AddToRecentlyPlayedAsync(MediaItem item)
        {
            // Remove if already exists to avoid duplicates
            var existing = _recentlyPlayed.FirstOrDefault(i => i.Id == item.Id);
            if (existing != null)
                _recentlyPlayed.Remove(existing);

            _recentlyPlayed.Add(item);

            // Keep only last 50 items
            while (_recentlyPlayed.Count > 50)
                _recentlyPlayed.RemoveAt(0);

            return Task.CompletedTask;
        }
        #endregion

        #region Protected Methods
        protected void SetState(PlaybackState newState, string? errorMessage = null)
        {
            var oldState = _state;
            _state = newState;
            OnPlaybackStateChanged(oldState, newState, errorMessage);
        }

        protected virtual void OnPlaybackStateChanged(PlaybackState oldState, PlaybackState newState, string? errorMessage = null)
        {
            PlaybackStateChanged?.Invoke(this, new PlaybackStateChangedEventArgs(oldState, newState, errorMessage));
        }

        protected virtual void OnMediaItemChanged(MediaItem? previousItem, MediaItem? currentItem)
        {
            MediaItemChanged?.Invoke(this, new MediaItemChangedEventArgs(previousItem, currentItem));
        }

        protected virtual void OnPositionChanged(TimeSpan position)
        {
            PositionChanged?.Invoke(this, position);
        }

        private void OnPositionTimerElapsed(object? sender, System.Timers.ElapsedEventArgs e)
        {
            if (_state == PlaybackState.Playing)
            {
                _position = GetCurrentPosition();
                OnPositionChanged(_position);

                // Check if track ended
                if (_position >= Duration && Duration > TimeSpan.Zero)
                {
                    Task.Run(async () =>
                    {
                        if (_isRepeatEnabled && _queue.Count == 1)
                        {
                            await SeekAsync(TimeSpan.Zero);
                        }
                        else
                        {
                            await NextTrackAsync();
                        }
                    });
                }
            }
        }
        #endregion

        public virtual void Dispose()
        {
            _positionTimer?.Stop();
            _positionTimer?.Dispose();
        }
    }
}