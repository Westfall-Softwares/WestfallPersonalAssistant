using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using WestfallPersonalAssistant.Services;

namespace WestfallPersonalAssistant.Tests
{
    public class FileUtilsTests : IDisposable
    {
        private readonly string _tempDirectory;

        public FileUtilsTests()
        {
            _tempDirectory = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
            Directory.CreateDirectory(_tempDirectory);
        }

        public void Dispose()
        {
            if (Directory.Exists(_tempDirectory))
            {
                Directory.Delete(_tempDirectory, true);
            }
        }

        [Fact]
        public async Task ReadTextAsync_WithValidFile_ShouldReturnContent()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "test.txt");
            const string expectedContent = "Hello, World!";
            await File.WriteAllTextAsync(filePath, expectedContent);

            // Act
            var content = await FileUtils.ReadTextAsync(filePath);

            // Assert
            Assert.Equal(expectedContent, content);
        }

        [Fact]
        public async Task ReadTextAsync_WithNonExistentFile_ShouldThrowFileNotFoundException()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "nonexistent.txt");

            // Act & Assert
            await Assert.ThrowsAsync<FileNotFoundException>(() => FileUtils.ReadTextAsync(filePath));
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        public async Task ReadTextAsync_WithInvalidPath_ShouldThrowArgumentException(string invalidPath)
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => FileUtils.ReadTextAsync(invalidPath));
        }

        [Fact]
        public async Task WriteTextAsync_WithValidPath_ShouldCreateFileWithContent()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "output.txt");
            const string content = "Test content for file";

            // Act
            await FileUtils.WriteTextAsync(filePath, content);

            // Assert
            Assert.True(File.Exists(filePath));
            var readContent = await File.ReadAllTextAsync(filePath);
            Assert.Equal(content, readContent);
        }

        [Fact]
        public async Task WriteTextAsync_WithNestedDirectory_ShouldCreateDirectoryAndFile()
        {
            // Arrange
            var nestedPath = Path.Combine(_tempDirectory, "nested", "deep", "file.txt");
            const string content = "Nested file content";

            // Act
            await FileUtils.WriteTextAsync(nestedPath, content);

            // Assert
            Assert.True(File.Exists(nestedPath));
            var readContent = await File.ReadAllTextAsync(nestedPath);
            Assert.Equal(content, readContent);
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        public async Task WriteTextAsync_WithInvalidPath_ShouldThrowArgumentException(string invalidPath)
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => FileUtils.WriteTextAsync(invalidPath, "content"));
        }

        [Fact]
        public async Task WriteTextAsync_WithNullContent_ShouldThrowArgumentNullException()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "test.txt");

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentNullException>(() => FileUtils.WriteTextAsync(filePath, null));
        }

        [Fact]
        public async Task ReadBytesAsync_WithValidFile_ShouldReturnCorrectBytes()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "binary.bin");
            var expectedBytes = new byte[] { 0x01, 0x02, 0x03, 0x04, 0xFF };
            await File.WriteAllBytesAsync(filePath, expectedBytes);

            // Act
            var bytes = await FileUtils.ReadBytesAsync(filePath);

            // Assert
            Assert.Equal(expectedBytes, bytes);
        }

        [Fact]
        public async Task WriteBytesAsync_WithValidData_ShouldCreateFileWithCorrectBytes()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "output.bin");
            var bytes = new byte[] { 0xDE, 0xAD, 0xBE, 0xEF };

            // Act
            await FileUtils.WriteBytesAsync(filePath, bytes);

            // Assert
            Assert.True(File.Exists(filePath));
            var readBytes = await File.ReadAllBytesAsync(filePath);
            Assert.Equal(bytes, readBytes);
        }

        [Fact]
        public async Task WriteBytesAsync_WithNullBytes_ShouldThrowArgumentNullException()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "test.bin");

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentNullException>(() => FileUtils.WriteBytesAsync(filePath, null));
        }

        [Theory]
        [InlineData("valid/path/file.txt", true)]
        [InlineData("simple.txt", true)]
        [InlineData("", false)]
        [InlineData(null, false)]
        [InlineData("   ", false)]
        public void IsValidPath_ShouldValidatePathsCorrectly(string path, bool expectedResult)
        {
            // Act
            var result = FileUtils.IsValidPath(path);

            // Assert
            Assert.Equal(expectedResult, result);
        }

        [Fact]
        public async Task CopyFileAsync_WithValidSourceAndDestination_ShouldCopyFile()
        {
            // Arrange
            var sourcePath = Path.Combine(_tempDirectory, "source.txt");
            var destinationPath = Path.Combine(_tempDirectory, "destination.txt");
            const string content = "File to copy";
            await File.WriteAllTextAsync(sourcePath, content);

            // Act
            await FileUtils.CopyFileAsync(sourcePath, destinationPath);

            // Assert
            Assert.True(File.Exists(destinationPath));
            var copiedContent = await File.ReadAllTextAsync(destinationPath);
            Assert.Equal(content, copiedContent);
        }

        [Fact]
        public async Task CopyFileAsync_WithNonExistentSource_ShouldThrowFileNotFoundException()
        {
            // Arrange
            var sourcePath = Path.Combine(_tempDirectory, "nonexistent.txt");
            var destinationPath = Path.Combine(_tempDirectory, "destination.txt");

            // Act & Assert
            await Assert.ThrowsAsync<FileNotFoundException>(() => FileUtils.CopyFileAsync(sourcePath, destinationPath));
        }

        [Fact]
        public async Task CopyFileAsync_WithExistingDestinationAndOverwriteDisabled_ShouldThrowInvalidOperationException()
        {
            // Arrange
            var sourcePath = Path.Combine(_tempDirectory, "source.txt");
            var destinationPath = Path.Combine(_tempDirectory, "destination.txt");
            await File.WriteAllTextAsync(sourcePath, "source content");
            await File.WriteAllTextAsync(destinationPath, "existing content");

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => 
                FileUtils.CopyFileAsync(sourcePath, destinationPath, overwrite: false));
        }

        [Fact]
        public async Task CopyFileAsync_WithExistingDestinationAndOverwriteEnabled_ShouldOverwriteFile()
        {
            // Arrange
            var sourcePath = Path.Combine(_tempDirectory, "source.txt");
            var destinationPath = Path.Combine(_tempDirectory, "destination.txt");
            const string sourceContent = "new content";
            await File.WriteAllTextAsync(sourcePath, sourceContent);
            await File.WriteAllTextAsync(destinationPath, "old content");

            // Act
            await FileUtils.CopyFileAsync(sourcePath, destinationPath, overwrite: true);

            // Assert
            var copiedContent = await File.ReadAllTextAsync(destinationPath);
            Assert.Equal(sourceContent, copiedContent);
        }

        [Fact]
        public void DeleteFileIfExists_WithExistingFile_ShouldDeleteFile()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "delete_me.txt");
            File.WriteAllText(filePath, "content");
            Assert.True(File.Exists(filePath));

            // Act
            FileUtils.DeleteFileIfExists(filePath);

            // Assert
            Assert.False(File.Exists(filePath));
        }

        [Fact]
        public void DeleteFileIfExists_WithNonExistentFile_ShouldNotThrow()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "nonexistent.txt");

            // Act & Assert - Should not throw
            FileUtils.DeleteFileIfExists(filePath);
        }

        [Fact]
        public void GetFileSize_WithExistingFile_ShouldReturnCorrectSize()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "size_test.txt");
            const string content = "1234567890"; // 10 bytes
            File.WriteAllText(filePath, content);

            // Act
            var size = FileUtils.GetFileSize(filePath);

            // Assert
            Assert.Equal(10, size);
        }

        [Fact]
        public void GetFileSize_WithNonExistentFile_ShouldReturnZero()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "nonexistent.txt");

            // Act
            var size = FileUtils.GetFileSize(filePath);

            // Assert
            Assert.Equal(0, size);
        }

        [Fact]
        public void FileExists_WithExistingFile_ShouldReturnTrue()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "exists.txt");
            File.WriteAllText(filePath, "content");

            // Act
            var exists = FileUtils.FileExists(filePath);

            // Assert
            Assert.True(exists);
        }

        [Fact]
        public void FileExists_WithNonExistentFile_ShouldReturnFalse()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "nonexistent.txt");

            // Act
            var exists = FileUtils.FileExists(filePath);

            // Assert
            Assert.False(exists);
        }

        [Fact]
        public void EnsureDirectoryExists_WithNonExistentDirectory_ShouldCreateDirectory()
        {
            // Arrange
            var directoryPath = Path.Combine(_tempDirectory, "new_directory");

            // Act
            FileUtils.EnsureDirectoryExists(directoryPath);

            // Assert
            Assert.True(Directory.Exists(directoryPath));
        }

        [Fact]
        public void EnsureDirectoryExists_WithExistingDirectory_ShouldNotThrow()
        {
            // Arrange
            var directoryPath = Path.Combine(_tempDirectory, "existing_directory");
            Directory.CreateDirectory(directoryPath);

            // Act & Assert - Should not throw
            FileUtils.EnsureDirectoryExists(directoryPath);
            Assert.True(Directory.Exists(directoryPath));
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        public void EnsureDirectoryExists_WithInvalidPath_ShouldThrowArgumentException(string invalidPath)
        {
            // Act & Assert
            Assert.Throws<ArgumentException>(() => FileUtils.EnsureDirectoryExists(invalidPath));
        }

        [Fact]
        public async Task ComputeFileHashAsync_WithSameContent_ShouldReturnSameHash()
        {
            // Arrange
            var file1 = Path.Combine(_tempDirectory, "file1.txt");
            var file2 = Path.Combine(_tempDirectory, "file2.txt");
            const string content = "identical content";
            await File.WriteAllTextAsync(file1, content);
            await File.WriteAllTextAsync(file2, content);

            // Act
            var hash1 = await FileUtils.ComputeFileHashAsync(file1);
            var hash2 = await FileUtils.ComputeFileHashAsync(file2);

            // Assert
            Assert.Equal(hash1, hash2);
            Assert.NotNull(hash1);
            Assert.NotEmpty(hash1);
        }

        [Fact]
        public async Task ComputeFileHashAsync_WithDifferentContent_ShouldReturnDifferentHashes()
        {
            // Arrange
            var file1 = Path.Combine(_tempDirectory, "file1.txt");
            var file2 = Path.Combine(_tempDirectory, "file2.txt");
            await File.WriteAllTextAsync(file1, "content 1");
            await File.WriteAllTextAsync(file2, "content 2");

            // Act
            var hash1 = await FileUtils.ComputeFileHashAsync(file1);
            var hash2 = await FileUtils.ComputeFileHashAsync(file2);

            // Assert
            Assert.NotEqual(hash1, hash2);
        }

        [Fact]
        public async Task ComputeFileHashAsync_WithNonExistentFile_ShouldThrowFileNotFoundException()
        {
            // Arrange
            var filePath = Path.Combine(_tempDirectory, "nonexistent.txt");

            // Act & Assert
            await Assert.ThrowsAsync<FileNotFoundException>(() => FileUtils.ComputeFileHashAsync(filePath));
        }
    }
}