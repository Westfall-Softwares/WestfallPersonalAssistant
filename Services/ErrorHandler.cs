using System;
using System.Threading.Tasks;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Interface for user notifications
    /// </summary>
    public interface IUserNotification
    {
        Task ShowErrorAsync(string message);
        Task ShowWarningAsync(string message);
        Task ShowInfoAsync(string message);
        Task ShowSuccessAsync(string message);
    }

    /// <summary>
    /// Centralized error handler to reduce code duplication and provide consistent error handling
    /// </summary>
    public class ErrorHandler
    {
        private readonly IUserNotification _notificationService;

        public ErrorHandler(IUserNotification notificationService)
        {
            _notificationService = notificationService ?? throw new ArgumentNullException(nameof(notificationService));
        }

        /// <summary>
        /// Handles async operations with comprehensive error handling and user notifications
        /// </summary>
        public async Task<Result<T>> HandleAsync<T>(
            Func<Task<T>> operation, 
            string operationName,
            string userFriendlyMessage = null)
        {
            userFriendlyMessage ??= $"{operationName} failed. Please try again.";
            
            try
            {
                Console.WriteLine($"{operationName} started");
                var result = await operation();
                Console.WriteLine($"{operationName} completed successfully");
                return Result<T>.Success(result);
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine($"{operationName} was cancelled");
                return Result<T>.Failure("Operation was cancelled.");
            }
            catch (UnauthorizedAccessException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to insufficient permissions: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Access denied during {operationName.ToLower()}. Please check your permissions.");
                return Result<T>.Failure("Access denied. Please check your permissions.");
            }
            catch (FileNotFoundException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed because a required file was not found: {ex.Message}");
                await _notificationService.ShowErrorAsync($"A required file was not found during {operationName.ToLower()}.");
                return Result<T>.Failure("Required file not found.");
            }
            catch (DirectoryNotFoundException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed because a required directory was not found: {ex.Message}");
                await _notificationService.ShowErrorAsync($"A required directory was not found during {operationName.ToLower()}.");
                return Result<T>.Failure("Required directory not found.");
            }
            catch (System.IO.IOException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to I/O error: {ex.Message}");
                await _notificationService.ShowErrorAsync($"File system error during {operationName.ToLower()}. Please try again.");
                return Result<T>.Failure("File system error occurred.");
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to invalid arguments: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Invalid input provided for {operationName.ToLower()}. Please check your data.");
                return Result<T>.Failure("Invalid input provided.");
            }
            catch (InvalidOperationException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to invalid operation state: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Operation cannot be completed at this time: {operationName.ToLower()}.");
                return Result<T>.Failure("Operation cannot be completed at this time.");
            }
            catch (TimeoutException ex)
            {
                Console.WriteLine($"WARNING: {operationName} timed out: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Operation timed out: {operationName.ToLower()}. Please try again.");
                return Result<T>.Failure("Operation timed out.");
            }
            catch (System.Net.Http.HttpRequestException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to network error: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Network error during {operationName.ToLower()}. Please check your connection.");
                return Result<T>.Failure("Network error occurred.");
            }
            catch (System.Security.SecurityException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to security violation: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Security error during {operationName.ToLower()}. Operation blocked for safety.");
                return Result<T>.Failure("Security error occurred.");
            }
            catch (OutOfMemoryException ex)
            {
                Console.WriteLine($"CRITICAL: {operationName} failed due to insufficient memory: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Insufficient memory for {operationName.ToLower()}. Please close other applications and try again.");
                return Result<T>.Failure("Insufficient memory available.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed with unexpected error: {ex.Message}");
                await _notificationService.ShowErrorAsync(userFriendlyMessage);
                return Result<T>.Failure(userFriendlyMessage);
            }
        }

        /// <summary>
        /// Handles async operations without return value
        /// </summary>
        public async Task<Result> HandleAsync(
            Func<Task> operation, 
            string operationName,
            string userFriendlyMessage = null)
        {
            userFriendlyMessage ??= $"{operationName} failed. Please try again.";
            
            try
            {
                Console.WriteLine($"{operationName} started");
                await operation();
                Console.WriteLine($"{operationName} completed successfully");
                return Result.Success();
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine($"{operationName} was cancelled");
                return Result.Failure("Operation was cancelled.");
            }
            catch (UnauthorizedAccessException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to insufficient permissions: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Access denied during {operationName.ToLower()}. Please check your permissions.");
                return Result.Failure("Access denied. Please check your permissions.");
            }
            catch (FileNotFoundException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed because a required file was not found: {ex.Message}");
                await _notificationService.ShowErrorAsync($"A required file was not found during {operationName.ToLower()}.");
                return Result.Failure("Required file not found.");
            }
            catch (DirectoryNotFoundException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed because a required directory was not found: {ex.Message}");
                await _notificationService.ShowErrorAsync($"A required directory was not found during {operationName.ToLower()}.");
                return Result.Failure("Required directory not found.");
            }
            catch (System.IO.IOException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to I/O error: {ex.Message}");
                await _notificationService.ShowErrorAsync($"File system error during {operationName.ToLower()}. Please try again.");
                return Result.Failure("File system error occurred.");
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to invalid arguments: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Invalid input provided for {operationName.ToLower()}. Please check your data.");
                return Result.Failure("Invalid input provided.");
            }
            catch (InvalidOperationException ex)
            {
                Console.WriteLine($"WARNING: {operationName} failed due to invalid operation state: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Operation cannot be completed at this time: {operationName.ToLower()}.");
                return Result.Failure("Operation cannot be completed at this time.");
            }
            catch (TimeoutException ex)
            {
                Console.WriteLine($"WARNING: {operationName} timed out: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Operation timed out: {operationName.ToLower()}. Please try again.");
                return Result.Failure("Operation timed out.");
            }
            catch (System.Net.Http.HttpRequestException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to network error: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Network error during {operationName.ToLower()}. Please check your connection.");
                return Result.Failure("Network error occurred.");
            }
            catch (System.Security.SecurityException ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed due to security violation: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Security error during {operationName.ToLower()}. Operation blocked for safety.");
                return Result.Failure("Security error occurred.");
            }
            catch (OutOfMemoryException ex)
            {
                Console.WriteLine($"CRITICAL: {operationName} failed due to insufficient memory: {ex.Message}");
                await _notificationService.ShowErrorAsync($"Insufficient memory for {operationName.ToLower()}. Please close other applications and try again.");
                return Result.Failure("Insufficient memory available.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: {operationName} failed with unexpected error: {ex.Message}");
                await _notificationService.ShowErrorAsync(userFriendlyMessage);
                return Result.Failure(userFriendlyMessage);
            }
        }

        /// <summary>
        /// Handles synchronous operations with comprehensive error handling
        /// </summary>
        public async Task<Result<T>> HandleSync<T>(
            Func<T> operation, 
            string operationName,
            string userFriendlyMessage = null)
        {
            return await HandleAsync(() => Task.FromResult(operation()), operationName, userFriendlyMessage);
        }

        /// <summary>
        /// Handles synchronous operations without return value
        /// </summary>
        public async Task<Result> HandleSync(
            Action operation, 
            string operationName,
            string userFriendlyMessage = null)
        {
            return await HandleAsync(() => 
            {
                operation();
                return Task.CompletedTask;
            }, operationName, userFriendlyMessage);
        }

        /// <summary>
        /// Handles operations with custom error mapping
        /// </summary>
        public async Task<Result<T>> HandleWithCustomMapping<T>(
            Func<Task<T>> operation,
            string operationName,
            Func<Exception, (string userMessage, string logMessage)> errorMapper = null)
        {
            try
            {
                Console.WriteLine($"{operationName} started");
                var result = await operation();
                Console.WriteLine($"{operationName} completed successfully");
                return Result<T>.Success(result);
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine($"{operationName} was cancelled");
                return Result<T>.Failure("Operation was cancelled.");
            }
            catch (Exception ex)
            {
                string userMessage;
                string logMessage;

                if (errorMapper != null)
                {
                    var mapped = errorMapper(ex);
                    userMessage = mapped.userMessage;
                    logMessage = mapped.logMessage;
                }
                else
                {
                    userMessage = $"{operationName} failed. Please try again.";
                    logMessage = $"{operationName} failed with unexpected error";
                }

                Console.WriteLine($"ERROR: {logMessage}: {ex.Message}");
                await _notificationService.ShowErrorAsync(userMessage);
                return Result<T>.Failure(userMessage);
            }
        }
    }

    /// <summary>
    /// Simple console-based user notification implementation for demonstration
    /// In a real application, this would integrate with the UI framework
    /// </summary>
    public class ConsoleUserNotification : IUserNotification
    {
        public Task ShowErrorAsync(string message)
        {
            Console.WriteLine($"ERROR: {message}");
            return Task.CompletedTask;
        }

        public Task ShowWarningAsync(string message)
        {
            Console.WriteLine($"WARNING: {message}");
            return Task.CompletedTask;
        }

        public Task ShowInfoAsync(string message)
        {
            Console.WriteLine($"INFO: {message}");
            return Task.CompletedTask;
        }

        public Task ShowSuccessAsync(string message)
        {
            Console.WriteLine($"SUCCESS: {message}");
            return Task.CompletedTask;
        }
    }
}