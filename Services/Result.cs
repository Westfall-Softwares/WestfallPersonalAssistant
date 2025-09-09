using System;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Result pattern for consistent error handling with user-friendly messages
    /// </summary>
    public class Result<T>
    {
        public bool IsSuccess { get; private set; }
        public T? Value { get; private set; }
        public string ErrorMessage { get; private set; } = string.Empty;
        public Exception? Exception { get; private set; }

        private Result(bool isSuccess, T? value, string errorMessage, Exception? exception = null)
        {
            IsSuccess = isSuccess;
            Value = value;
            ErrorMessage = errorMessage;
            Exception = exception;
        }

        public static Result<T> Success(T value) => new(true, value, string.Empty);
        public static Result<T> Failure(string errorMessage) => new(false, default, errorMessage);
        public static Result<T> Failure(string errorMessage, Exception exception) => new(false, default, errorMessage, exception);
    }

    /// <summary>
    /// Result pattern for operations that don't return a value
    /// </summary>
    public class Result
    {
        public bool IsSuccess { get; private set; }
        public string ErrorMessage { get; private set; } = string.Empty;
        public Exception? Exception { get; private set; }

        private Result(bool isSuccess, string errorMessage, Exception? exception = null)
        {
            IsSuccess = isSuccess;
            ErrorMessage = errorMessage;
            Exception = exception;
        }

        public static Result Success() => new(true, string.Empty);
        public static Result Failure(string errorMessage) => new(false, errorMessage);
        public static Result Failure(string errorMessage, Exception exception) => new(false, errorMessage, exception);
    }

    /// <summary>
    /// Exception handler utility for consistent user-friendly error messages
    /// </summary>
    public static class ExceptionHandler
    {
        public static async Task<Result<T>> TryExecuteAsync<T>(Func<Task<T>> operation, string userErrorMessage)
        {
            try
            {
                var result = await operation().ConfigureAwait(false);
                return Result<T>.Success(result);
            }
            catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
            {
                return Result<T>.Failure("The operation timed out. Please try again.", ex);
            }
            catch (TaskCanceledException ex)
            {
                return Result<T>.Failure("The operation was cancelled.", ex);
            }
            catch (OperationCanceledException ex)
            {
                return Result<T>.Failure("The operation was cancelled.", ex);
            }
            catch (TimeoutException ex)
            {
                return Result<T>.Failure("The operation timed out. Please try again.", ex);
            }
            catch (OutOfMemoryException ex)
            {
                return Result<T>.Failure("Out of memory. Please close other applications and try again.", ex);
            }
            catch (UnauthorizedAccessException ex)
            {
                return Result<T>.Failure("Access denied. Please check your permissions.", ex);
            }
            catch (FileNotFoundException ex)
            {
                return Result<T>.Failure("The requested file could not be found.", ex);
            }
            catch (DirectoryNotFoundException ex)
            {
                return Result<T>.Failure("The requested directory could not be found.", ex);
            }
            catch (IOException ex)
            {
                return Result<T>.Failure("An error occurred while accessing the file system.", ex);
            }
            catch (ArgumentException ex)
            {
                return Result<T>.Failure("Invalid input provided. Please check your data.", ex);
            }
            catch (InvalidOperationException ex)
            {
                return Result<T>.Failure("The operation cannot be completed at this time.", ex);
            }
            catch (System.Net.Http.HttpRequestException ex)
            {
                return Result<T>.Failure("Service is temporarily unavailable. Please try again later.", ex);
            }
            catch (System.Net.WebException ex)
            {
                return Result<T>.Failure("Network request failed. Please check your internet connection.", ex);
            }
            catch (System.Net.NetworkInformation.NetworkInformationException ex)
            {
                return Result<T>.Failure("Network error occurred. Please check your connection.", ex);
            }
            catch (Exception ex)
            {
                // Log the technical error details
                Console.WriteLine($"Unexpected error: {ex}");
                return Result<T>.Failure(userErrorMessage, ex);
            }
        }

        public static async Task<Result> TryExecuteAsync(Func<Task> operation, string userErrorMessage)
        {
            try
            {
                await operation().ConfigureAwait(false);
                return Result.Success();
            }
            catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
            {
                return Result.Failure("The operation timed out. Please try again.", ex);
            }
            catch (TaskCanceledException ex)
            {
                return Result.Failure("The operation was cancelled.", ex);
            }
            catch (OperationCanceledException ex)
            {
                return Result.Failure("The operation was cancelled.", ex);
            }
            catch (TimeoutException ex)
            {
                return Result.Failure("The operation timed out. Please try again.", ex);
            }
            catch (OutOfMemoryException ex)
            {
                return Result.Failure("Out of memory. Please close other applications and try again.", ex);
            }
            catch (UnauthorizedAccessException ex)
            {
                return Result.Failure("Access denied. Please check your permissions.", ex);
            }
            catch (FileNotFoundException ex)
            {
                return Result.Failure("The requested file could not be found.", ex);
            }
            catch (DirectoryNotFoundException ex)
            {
                return Result.Failure("The requested directory could not be found.", ex);
            }
            catch (IOException ex)
            {
                return Result.Failure("An error occurred while accessing the file system.", ex);
            }
            catch (ArgumentException ex)
            {
                return Result.Failure("Invalid input provided. Please check your data.", ex);
            }
            catch (InvalidOperationException ex)
            {
                return Result.Failure("The operation cannot be completed at this time.", ex);
            }
            catch (System.Net.Http.HttpRequestException ex)
            {
                return Result.Failure("Service is temporarily unavailable. Please try again later.", ex);
            }
            catch (System.Net.WebException ex)
            {
                return Result.Failure("Network request failed. Please check your internet connection.", ex);
            }
            catch (System.Net.NetworkInformation.NetworkInformationException ex)
            {
                return Result.Failure("Network error occurred. Please check your connection.", ex);
            }
            catch (Exception ex)
            {
                // Log the technical error details
                Console.WriteLine($"Unexpected error: {ex}");
                return Result.Failure(userErrorMessage, ex);
            }
        }

        public static Result<T> TryExecute<T>(Func<T> operation, string userErrorMessage)
        {
            try
            {
                var result = operation();
                return Result<T>.Success(result);
            }
            catch (UnauthorizedAccessException ex)
            {
                return Result<T>.Failure("Access denied. Please check your permissions.", ex);
            }
            catch (FileNotFoundException ex)
            {
                return Result<T>.Failure("The requested file could not be found.", ex);
            }
            catch (DirectoryNotFoundException ex)
            {
                return Result<T>.Failure("The requested directory could not be found.", ex);
            }
            catch (IOException ex)
            {
                return Result<T>.Failure("An error occurred while accessing the file system.", ex);
            }
            catch (ArgumentException ex)
            {
                return Result<T>.Failure("Invalid input provided. Please check your data.", ex);
            }
            catch (InvalidOperationException ex)
            {
                return Result<T>.Failure("The operation cannot be completed at this time.", ex);
            }
            catch (Exception ex)
            {
                // Log the technical error details
                Console.WriteLine($"Unexpected error: {ex}");
                return Result<T>.Failure(userErrorMessage, ex);
            }
        }
    }
}