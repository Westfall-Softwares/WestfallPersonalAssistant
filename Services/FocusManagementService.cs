using System;
using System.Collections.Generic;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;

namespace WestfallPersonalAssistant.Services
{
    /// <summary>
    /// Service for managing focus and keyboard navigation accessibility features
    /// </summary>
    public interface IFocusManagementService
    {
        // Focus trapping for modal dialogs
        void EnableFocusTrapping(Control container);
        void DisableFocusTrapping(Control container);
        
        // Focus management
        void MoveFocusToNext();
        void MoveFocusToPrevious();
        void MoveFocusToFirst(Control container);
        void MoveFocusToLast(Control container);
        
        // Keyboard shortcuts
        void RegisterGlobalKeyboardShortcut(KeyGesture gesture, Action action, string description);
        void UnregisterGlobalKeyboardShortcut(KeyGesture gesture);
        Dictionary<KeyGesture, string> GetRegisteredShortcuts();
        
        // Accessibility announcements for focus changes
        event Action<string>? FocusChanged;
    }

    /// <summary>
    /// Implementation of focus management service for enhanced accessibility
    /// </summary>
    public class FocusManagementService : IFocusManagementService
    {
        private readonly Dictionary<Control, bool> _focusTrappedContainers = new();
        private readonly Dictionary<KeyGesture, (Action Action, string Description)> _globalShortcuts = new();
        
        public event Action<string>? FocusChanged;

        public void EnableFocusTrapping(Control container)
        {
            if (container == null) return;
            
            _focusTrappedContainers[container] = true;
            
            container.KeyDown += OnContainerKeyDown;
            container.AttachedToVisualTree += OnContainerAttached;
            container.DetachedFromVisualTree += OnContainerDetached;
        }

        public void DisableFocusTrapping(Control container)
        {
            if (container == null) return;
            
            _focusTrappedContainers.Remove(container);
            
            container.KeyDown -= OnContainerKeyDown;
            container.AttachedToVisualTree -= OnContainerAttached;
            container.DetachedFromVisualTree -= OnContainerDetached;
        }

        private void OnContainerKeyDown(object? sender, KeyEventArgs e)
        {
            if (sender is not Control container || !_focusTrappedContainers.ContainsKey(container))
                return;

            if (e.Key == Key.Tab)
            {
                var isShiftPressed = e.KeyModifiers.HasFlag(KeyModifiers.Shift);
                
                if (isShiftPressed)
                {
                    if (IsFirstFocusableElement(container))
                    {
                        MoveFocusToLast(container);
                        e.Handled = true;
                    }
                }
                else
                {
                    if (IsLastFocusableElement(container))
                    {
                        MoveFocusToFirst(container);
                        e.Handled = true;
                    }
                }
            }
            else if (e.Key == Key.Escape)
            {
                // Close dialog or return focus to previous element
                FocusChanged?.Invoke("Dialog closed with Escape key");
            }
        }

        private void OnContainerAttached(object? sender, Avalonia.VisualTreeAttachmentEventArgs e)
        {
            if (sender is Control container)
            {
                MoveFocusToFirst(container);
                FocusChanged?.Invoke("Modal dialog opened");
            }
        }

        private void OnContainerDetached(object? sender, Avalonia.VisualTreeAttachmentEventArgs e)
        {
            if (sender is Control container)
            {
                DisableFocusTrapping(container);
            }
        }

        public void MoveFocusToNext()
        {
            // Simplified implementation for now
            try
            {
                FocusChanged?.Invoke("Focus moved to next element");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error moving focus to next element: {ex.Message}");
            }
        }

        public void MoveFocusToPrevious()
        {
            try
            {
                FocusChanged?.Invoke("Focus moved to previous element");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error moving focus to previous element: {ex.Message}");
            }
        }

        public void MoveFocusToFirst(Control container)
        {
            try
            {
                var firstFocusable = GetFirstFocusableElement(container);
                firstFocusable?.Focus();
                
                if (firstFocusable != null)
                {
                    FocusChanged?.Invoke($"Focus moved to first element: {GetElementDescription(firstFocusable)}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error moving focus to first element: {ex.Message}");
            }
        }

        public void MoveFocusToLast(Control container)
        {
            try
            {
                var lastFocusable = GetLastFocusableElement(container);
                lastFocusable?.Focus();
                
                if (lastFocusable != null)
                {
                    FocusChanged?.Invoke($"Focus moved to last element: {GetElementDescription(lastFocusable)}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error moving focus to last element: {ex.Message}");
            }
        }

        public void RegisterGlobalKeyboardShortcut(KeyGesture gesture, Action action, string description)
        {
            _globalShortcuts[gesture] = (action, description);
        }

        public void UnregisterGlobalKeyboardShortcut(KeyGesture gesture)
        {
            _globalShortcuts.Remove(gesture);
        }

        public Dictionary<KeyGesture, string> GetRegisteredShortcuts()
        {
            var shortcuts = new Dictionary<KeyGesture, string>();
            foreach (var kvp in _globalShortcuts)
            {
                shortcuts[kvp.Key] = kvp.Value.Description;
            }
            return shortcuts;
        }

        private Control? GetFirstFocusableElement(Control container)
        {
            return FindFocusableElements(container).FirstOrDefault();
        }

        private Control? GetLastFocusableElement(Control container)
        {
            return FindFocusableElements(container).LastOrDefault();
        }

        private bool IsFirstFocusableElement(Control container)
        {
            try
            {
                var firstElement = GetFirstFocusableElement(container);
                return firstElement != null;
            }
            catch
            {
                return false;
            }
        }

        private bool IsLastFocusableElement(Control container)
        {
            try
            {
                var lastElement = GetLastFocusableElement(container);
                return lastElement != null;
            }
            catch
            {
                return false;
            }
        }

        private Control? GetNextFocusableElement(Control current)
        {
            // Simplified implementation - in a real scenario, this would
            // traverse the visual tree according to tab order
            return null;
        }

        private Control? GetPreviousFocusableElement(Control current)
        {
            // Simplified implementation - in a real scenario, this would
            // traverse the visual tree according to tab order
            return null;
        }

        private List<Control> FindFocusableElements(Control container)
        {
            var focusableElements = new List<Control>();
            
            try
            {
                // This is a simplified implementation
                // In a real scenario, this would recursively traverse the visual tree
                // and find all focusable elements in the correct tab order
                
                if (container is Panel panel)
                {
                    foreach (var child in panel.Children)
                    {
                        if (child is Control control && control.Focusable && control.IsVisible && control.IsEnabled)
                        {
                            focusableElements.Add(control);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error finding focusable elements: {ex.Message}");
            }
            
            return focusableElements;
        }

        private string GetElementDescription(Control element)
        {
            // Get a description for screen reader announcements
            try
            {
                var name = Avalonia.Automation.AutomationProperties.GetName(element);
                if (!string.IsNullOrEmpty(name))
                    return name;
                
                var className = element.GetType().Name;
                return className;
            }
            catch
            {
                return "element";
            }
        }
    }
}