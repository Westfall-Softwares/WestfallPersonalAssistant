/**
 * Settings Management JavaScript for Westfall Personal Assistant
 * 
 * Handles settings form interactions, API key testing, and settings persistence.
 */

class SettingsManager {
    constructor() {
        this.init();
    }
    
    init() {
        // Initialize event listeners
        this.setupEventListeners();
        
        // Load current settings status
        this.loadSettingsStatus();
    }
    
    setupEventListeners() {
        // Auto-save on input change (with debouncing)
        const inputs = document.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.debounce(this.autoSave.bind(this), 1000)();
            });
        });
        
        // API key visibility toggle
        this.setupPasswordToggle();
    }
    
    setupPasswordToggle() {
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.innerHTML = '👁️';
            toggleBtn.className = 'password-toggle';
            toggleBtn.style.cssText = `
                margin-left: 5px;
                padding: 5px 10px;
                border: 1px solid #ced4da;
                background: #f8f9fa;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            `;
            
            toggleBtn.onclick = () => {
                if (input.type === 'password') {
                    input.type = 'text';
                    toggleBtn.innerHTML = '🙈';
                } else {
                    input.type = 'password';
                    toggleBtn.innerHTML = '👁️';
                }
            };
            
            input.parentNode.insertBefore(toggleBtn, input.nextSibling);
        });
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    autoSave() {
        // Optional: Auto-save settings when changed
        // For now, we'll just indicate changes are pending
        this.markUnsavedChanges();
    }
    
    markUnsavedChanges() {
        const saveButton = document.querySelector('.primary-button');
        if (saveButton && !saveButton.classList.contains('has-changes')) {
            saveButton.classList.add('has-changes');
            saveButton.style.background = 'linear-gradient(135deg, #f39c12, #e67e22)';
            saveButton.innerHTML = '💾 Save Changes *';
        }
    }
    
    clearUnsavedChanges() {
        const saveButton = document.querySelector('.primary-button');
        if (saveButton) {
            saveButton.classList.remove('has-changes');
            saveButton.style.background = '';
            saveButton.innerHTML = '💾 Save Settings';
        }
    }
    
    async loadSettingsStatus() {
        try {
            const response = await fetch('/api/settings/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateServiceStatus(data.services);
                this.updateConfigurationSummary(data);
            }
        } catch (error) {
            console.error('Error loading settings status:', error);
        }
    }
    
    updateServiceStatus(services) {
        Object.entries(services).forEach(([serviceKey, serviceData]) => {
            const statusElements = document.querySelectorAll(`#${serviceKey}-status`);
            statusElements.forEach(element => {
                if (element) {
                    const statusIndicator = element.querySelector('.service-status');
                    if (statusIndicator) {
                        statusIndicator.className = `service-status ${serviceData.configured ? 'configured' : 'not-configured'}`;
                    }
                }
            });
        });
    }
    
    updateConfigurationSummary(data) {
        // Create or update a configuration summary
        let summary = document.getElementById('config-summary');
        if (!summary) {
            summary = document.createElement('div');
            summary.id = 'config-summary';
            summary.style.cssText = `
                background: ${data.configuration_complete ? '#d4edda' : '#fff3cd'};
                border: 1px solid ${data.configuration_complete ? '#c3e6cb' : '#ffeaa7'};
                color: ${data.configuration_complete ? '#155724' : '#856404'};
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-weight: 500;
            `;
            
            const container = document.querySelector('.container');
            const navLinks = document.querySelector('.nav-links');
            container.insertBefore(summary, navLinks.nextSibling);
        }
        
        summary.innerHTML = `
            📊 Configuration Status: ${data.configured_services}/${data.total_services} services configured
            ${data.configuration_complete ? ' ✅ Ready to use!' : ' ⚠️ Additional setup recommended'}
        `;
    }
    
    async testApiKey(service) {
        let apiKeyInput;
        let statusElement;
        let testButton;
        
        // Find the relevant elements
        if (service === 'openweather') {
            apiKeyInput = document.getElementById('openweather-key');
            statusElement = document.getElementById('openweather-status');
            testButton = statusElement.parentNode.querySelector('.test-btn');
        } else if (service === 'newsapi') {
            apiKeyInput = document.getElementById('newsapi-key');
            statusElement = document.getElementById('newsapi-status');
            testButton = statusElement.parentNode.querySelector('.test-btn');
        } else if (service === 'openai') {
            apiKeyInput = document.getElementById('openai-key');
            statusElement = document.getElementById('openai-status');
            testButton = statusElement.parentNode.querySelector('.test-btn');
        }
        
        if (!apiKeyInput || !statusElement) {
            console.error(`Elements not found for service: ${service}`);
            return;
        }
        
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            this.showStatus(statusElement, 'Enter key first', 'warning');
            return;
        }
        
        // Disable test button during testing
        if (testButton) {
            testButton.disabled = true;
            testButton.innerHTML = 'Testing...';
        }
        
        // Show testing indicator
        this.showStatus(statusElement, 'Testing...', 'testing');
        
        try {
            const response = await fetch(`/api/settings/test/${service}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            const data = await response.json();
            
            if (data.success && data.valid) {
                this.showStatus(statusElement, '✅ Valid', 'success');
                this.showNotification(`${service.toUpperCase()} API key is valid!`, 'success');
            } else {
                this.showStatus(statusElement, '❌ Invalid', 'error');
                this.showNotification(`${service.toUpperCase()} API key is invalid. Please check the key.`, 'error');
            }
        } catch (error) {
            this.showStatus(statusElement, '❌ Error testing', 'error');
            this.showNotification(`Error testing ${service.toUpperCase()} API key: ${error.message}`, 'error');
            console.error('Error testing API key:', error);
        } finally {
            // Re-enable test button
            if (testButton) {
                testButton.disabled = false;
                testButton.innerHTML = 'Test';
            }
        }
    }
    
    showStatus(element, message, type) {
        element.innerHTML = `<span class="service-status ${type === 'success' ? 'configured' : 'not-configured'}"></span>${message}`;
        element.className = `status ${type}`;
    }
    
    async saveSettings() {
        const actionButtons = document.querySelector('.action-buttons');
        actionButtons.classList.add('saving');
        
        // Collect all settings
        const settings = this.collectSettings();
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Settings saved successfully!', 'success');
                this.clearUnsavedChanges();
                
                // Reload settings status
                setTimeout(() => {
                    this.loadSettingsStatus();
                }, 1000);
            } else {
                this.showNotification('Error saving settings: ' + (data.error || 'Unknown error'), 'error');
                console.error('Settings save error:', data);
            }
        } catch (error) {
            this.showNotification('Error saving settings: ' + error.message, 'error');
            console.error('Error saving settings:', error);
        } finally {
            actionButtons.classList.remove('saving');
        }
    }
    
    collectSettings() {
        return {
            // API Keys
            OPENWEATHER_API_KEY: this.getValue('openweather-key'),
            NEWSAPI_KEY: this.getValue('newsapi-key'),
            OPENAI_API_KEY: this.getValue('openai-key'),
            OPENAI_DEFAULT_MODEL: this.getValue('openai-model'),
            
            // Email settings
            EMAIL_SMTP_HOST: this.getValue('email-host'),
            EMAIL_SMTP_PORT: this.getValue('email-port'),
            EMAIL_USERNAME: this.getValue('email-username'),
            EMAIL_PASSWORD: this.getValue('email-password'),
            EMAIL_USE_TLS: this.getChecked('email-tls') ? 'true' : 'false',
            
            // AI Model settings
            OLLAMA_BASE_URL: this.getValue('ollama-url'),
            OLLAMA_DEFAULT_MODEL: this.getValue('ollama-model'),
            
            // Feature toggles
            ENABLE_VOICE: this.getChecked('enable-voice') ? 'true' : 'false',
            BUSINESS_FEATURES_ENABLED: this.getChecked('business-features') ? 'true' : 'false',
            SCREEN_CAPTURE_ENABLED: this.getChecked('screen-capture') ? 'true' : 'false',
            WEB_SEARCH_ENABLED: this.getChecked('web-search') ? 'true' : 'false',
            
            // UI settings
            THEME_MODE: this.getValue('theme-mode'),
            ENABLE_ANIMATIONS: this.getChecked('enable-animations') ? 'true' : 'false',
            
            // Security settings
            MAX_REQUESTS_PER_MINUTE: this.getValue('max-requests'),
            CONTENT_FILTERING_ENABLED: this.getChecked('content-filtering') ? 'true' : 'false'
        };
    }
    
    getValue(id) {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    }
    
    getChecked(id) {
        const element = document.getElementById(id);
        return element ? element.checked : false;
    }
    
    async resetSettings() {
        if (!confirm('Are you sure you want to reset all settings to default values? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/settings/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ confirm: true })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Settings reset to defaults successfully!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.showNotification('Error resetting settings: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('Error resetting settings: ' + error.message, 'error');
            console.error('Error resetting settings:', error);
        }
    }
    
    showNotification(message, type = 'success') {
        let notification = document.getElementById('notification');
        
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'notification';
            document.body.appendChild(notification);
        }
        
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
        
        // Allow manual close
        notification.onclick = () => {
            notification.style.display = 'none';
        };
    }
    
    // Validation helpers
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    validateUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    validatePort(port) {
        const portNum = parseInt(port);
        return portNum > 0 && portNum < 65536;
    }
    
    // Real-time validation
    setupValidation() {
        // Email validation
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value && !this.validateEmail(input.value)) {
                    input.style.borderColor = '#dc3545';
                    this.showNotification('Please enter a valid email address', 'error');
                } else {
                    input.style.borderColor = '#28a745';
                }
            });
        });
        
        // URL validation
        const urlInputs = document.querySelectorAll('input[type="url"]');
        urlInputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value && !this.validateUrl(input.value)) {
                    input.style.borderColor = '#dc3545';
                    this.showNotification('Please enter a valid URL', 'error');
                } else {
                    input.style.borderColor = '#28a745';
                }
            });
        });
        
        // Port validation
        const portInput = document.getElementById('email-port');
        if (portInput) {
            portInput.addEventListener('blur', () => {
                if (portInput.value && !this.validatePort(portInput.value)) {
                    portInput.style.borderColor = '#dc3545';
                    this.showNotification('Please enter a valid port number (1-65535)', 'error');
                } else {
                    portInput.style.borderColor = '#28a745';
                }
            });
        }
    }
}

// Global functions for inline event handlers (backward compatibility)
window.testApiKey = function(service) {
    if (window.settingsManager) {
        window.settingsManager.testApiKey(service);
    }
};

window.saveSettings = function() {
    if (window.settingsManager) {
        window.settingsManager.saveSettings();
    }
};

window.resetSettings = function() {
    if (window.settingsManager) {
        window.settingsManager.resetSettings();
    }
};

window.showNotification = function(message, type = 'success') {
    if (window.settingsManager) {
        window.settingsManager.showNotification(message, type);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.settingsManager = new SettingsManager();
    
    // Setup validation
    window.settingsManager.setupValidation();
    
    console.log('Settings Manager initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SettingsManager;
}