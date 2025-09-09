using System;
using System.ComponentModel;
using System.Threading.Tasks;
using System.Windows.Input;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.ViewModels
{
    /// <summary>
    /// ViewModel for media player controls
    /// </summary>
    public class MediaPlayerViewModel : INotifyPropertyChanged
    {
        private readonly MediaPlayerManager _mediaPlayerManager;
        private bool _isPlaying;
        private bool _isPaused;
        private string _currentTitle = "No media";
        private string _currentArtist = "";
        private TimeSpan _position;
        private TimeSpan _duration;
        private double _volume = 1.0;
        private bool _isMuted;
        private bool _isRepeatEnabled;
        private bool _isShuffleEnabled;

        public event PropertyChangedEventHandler? PropertyChanged;

        #region Properties
        public bool IsPlaying
        {
            get => _isPlaying;
            private set
            {
                _isPlaying = value;
                OnPropertyChanged(nameof(IsPlaying));
                OnPropertyChanged(nameof(PlayPauseText));
            }
        }

        public bool IsPaused
        {
            get => _isPaused;
            private set
            {
                _isPaused = value;
                OnPropertyChanged(nameof(IsPaused));
            }
        }

        public string CurrentTitle
        {
            get => _currentTitle;
            private set
            {
                _currentTitle = value;
                OnPropertyChanged(nameof(CurrentTitle));
            }
        }

        public string CurrentArtist
        {
            get => _currentArtist;
            private set
            {
                _currentArtist = value;
                OnPropertyChanged(nameof(CurrentArtist));
            }
        }

        public TimeSpan Position
        {
            get => _position;
            private set
            {
                _position = value;
                OnPropertyChanged(nameof(Position));
                OnPropertyChanged(nameof(PositionText));
                OnPropertyChanged(nameof(ProgressPercentage));
            }
        }

        public TimeSpan Duration
        {
            get => _duration;
            private set
            {
                _duration = value;
                OnPropertyChanged(nameof(Duration));
                OnPropertyChanged(nameof(DurationText));
                OnPropertyChanged(nameof(ProgressPercentage));
            }
        }

        public double Volume
        {
            get => _volume;
            set
            {
                _volume = Math.Max(0.0, Math.Min(1.0, value));
                _mediaPlayerManager.Volume = _volume;
                OnPropertyChanged(nameof(Volume));
                OnPropertyChanged(nameof(VolumePercentage));
            }
        }

        public bool IsMuted
        {
            get => _isMuted;
            set
            {
                _isMuted = value;
                _mediaPlayerManager.IsMuted = _isMuted;
                OnPropertyChanged(nameof(IsMuted));
                OnPropertyChanged(nameof(MuteButtonText));
            }
        }

        public bool IsRepeatEnabled
        {
            get => _isRepeatEnabled;
            set
            {
                _isRepeatEnabled = value;
                _mediaPlayerManager.IsRepeatEnabled = _isRepeatEnabled;
                OnPropertyChanged(nameof(IsRepeatEnabled));
            }
        }

        public bool IsShuffleEnabled
        {
            get => _isShuffleEnabled;
            set
            {
                _isShuffleEnabled = value;
                _mediaPlayerManager.IsShuffleEnabled = _isShuffleEnabled;
                OnPropertyChanged(nameof(IsShuffleEnabled));
            }
        }

        // Computed properties
        public string PlayPauseText => IsPlaying ? "⏸" : "▶";
        public string MuteButtonText => IsMuted ? "🔇" : "🔊";
        public string PositionText => Position.ToString(@"mm\:ss");
        public string DurationText => Duration.ToString(@"mm\:ss");
        public int VolumePercentage => (int)(Volume * 100);
        public double ProgressPercentage => Duration.TotalSeconds > 0 ? (Position.TotalSeconds / Duration.TotalSeconds) * 100 : 0;
        #endregion

        #region Commands
        public ICommand PlayPauseCommand { get; }
        public ICommand StopCommand { get; }
        public ICommand NextCommand { get; }
        public ICommand PreviousCommand { get; }
        public ICommand ToggleMuteCommand { get; }
        public ICommand ToggleRepeatCommand { get; }
        public ICommand ToggleShuffleCommand { get; }
        #endregion

        public MediaPlayerViewModel(MediaPlayerManager mediaPlayerManager)
        {
            _mediaPlayerManager = mediaPlayerManager ?? throw new ArgumentNullException(nameof(mediaPlayerManager));

            // Subscribe to player events
            _mediaPlayerManager.PlaybackStateChanged += OnPlaybackStateChanged;
            _mediaPlayerManager.MediaItemChanged += OnMediaItemChanged;
            _mediaPlayerManager.PositionChanged += OnPositionChanged;

            // Initialize commands
            PlayPauseCommand = new RelayCommand(async () => await PlayPauseAsync());
            StopCommand = new RelayCommand(async () => await StopAsync());
            NextCommand = new RelayCommand(async () => await NextAsync());
            PreviousCommand = new RelayCommand(async () => await PreviousAsync());
            ToggleMuteCommand = new RelayCommand(() => IsMuted = !IsMuted);
            ToggleRepeatCommand = new RelayCommand(() => IsRepeatEnabled = !IsRepeatEnabled);
            ToggleShuffleCommand = new RelayCommand(() => IsShuffleEnabled = !IsShuffleEnabled);

            // Initialize state
            UpdateFromManager();
        }

        #region Command Implementations
        private async Task PlayPauseAsync()
        {
            try
            {
                if (IsPlaying)
                {
                    await _mediaPlayerManager.PauseAsync();
                }
                else if (IsPaused)
                {
                    await _mediaPlayerManager.ResumeAsync();
                }
                // If stopped and no current item, we can't play anything
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in PlayPause: {ex.Message}");
            }
        }

        private async Task StopAsync()
        {
            try
            {
                await _mediaPlayerManager.StopAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in Stop: {ex.Message}");
            }
        }

        private async Task NextAsync()
        {
            try
            {
                await _mediaPlayerManager.NextTrackAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in Next: {ex.Message}");
            }
        }

        private async Task PreviousAsync()
        {
            try
            {
                await _mediaPlayerManager.PreviousTrackAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in Previous: {ex.Message}");
            }
        }
        #endregion

        #region Event Handlers
        private void OnPlaybackStateChanged(object? sender, PlaybackStateChangedEventArgs e)
        {
            IsPlaying = e.NewState == PlaybackState.Playing;
            IsPaused = e.NewState == PlaybackState.Paused;
        }

        private void OnMediaItemChanged(object? sender, MediaItemChangedEventArgs e)
        {
            if (e.CurrentItem != null)
            {
                CurrentTitle = e.CurrentItem.Title;
                CurrentArtist = e.CurrentItem.Artist;
                Duration = e.CurrentItem.Duration;
            }
            else
            {
                CurrentTitle = "No media";
                CurrentArtist = "";
                Duration = TimeSpan.Zero;
            }
        }

        private void OnPositionChanged(object? sender, TimeSpan position)
        {
            Position = position;
        }
        #endregion

        #region Public Methods
        public async Task PlayMediaItemAsync(MediaItem item)
        {
            try
            {
                await _mediaPlayerManager.PlayAsync(item);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error playing media item: {ex.Message}");
            }
        }

        public async Task SeekAsync(double progressPercentage)
        {
            if (Duration.TotalSeconds > 0)
            {
                var newPosition = TimeSpan.FromSeconds(Duration.TotalSeconds * (progressPercentage / 100.0));
                try
                {
                    await _mediaPlayerManager.SeekAsync(newPosition);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error seeking: {ex.Message}");
                }
            }
        }
        #endregion

        private void UpdateFromManager()
        {
            IsPlaying = _mediaPlayerManager.IsPlaying;
            IsPaused = _mediaPlayerManager.State == PlaybackState.Paused;
            Position = _mediaPlayerManager.Position;
            Duration = _mediaPlayerManager.Duration;
            Volume = _mediaPlayerManager.Volume;
            IsMuted = _mediaPlayerManager.IsMuted;
            IsRepeatEnabled = _mediaPlayerManager.IsRepeatEnabled;
            IsShuffleEnabled = _mediaPlayerManager.IsShuffleEnabled;

            if (_mediaPlayerManager.CurrentItem != null)
            {
                CurrentTitle = _mediaPlayerManager.CurrentItem.Title;
                CurrentArtist = _mediaPlayerManager.CurrentItem.Artist;
            }
        }

        private void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public void Dispose()
        {
            _mediaPlayerManager.PlaybackStateChanged -= OnPlaybackStateChanged;
            _mediaPlayerManager.MediaItemChanged -= OnMediaItemChanged;
            _mediaPlayerManager.PositionChanged -= OnPositionChanged;
        }
    }
}