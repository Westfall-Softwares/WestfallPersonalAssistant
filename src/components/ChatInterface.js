import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  Alert,
  Fab,
  Menu,
  MenuItem,
  Tooltip,
  Button
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  NewReleases as NewIcon,
  MoreVert as MoreVertIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import ConversationHistory from './ConversationHistory';

const ipcRenderer = window.electronAPI?.ipcRenderer;

const ChatInterface = ({ thinkingMode, modelStatus }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversationTitle, setConversationTitle] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Generate new conversation ID
  const generateConversationId = () => {
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  // Listen for IPC events
  useEffect(() => {
    const handleFocusChat = () => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    };

    if (ipcRenderer) {
      ipcRenderer.on('focus-chat', handleFocusChat);
      return () => ipcRenderer.removeListener('focus-chat', handleFocusChat);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    
    // Mark as having unsaved changes when new messages are added
    if (messages.length > 0) {
      setHasUnsavedChanges(true);
    }
  }, [messages]);

  // Auto-save conversation periodically
  useEffect(() => {
    if (messages.length > 0 && conversationId) {
      const saveInterval = setInterval(() => {
        saveConversation();
      }, 30000); // Auto-save every 30 seconds

      return () => clearInterval(saveInterval);
    }
  }, [messages, conversationId]);

  const saveConversation = async () => {
    if (!conversationId || messages.length === 0) return;

    try {
      const conversation = {
        id: conversationId,
        title: conversationTitle || generateTitle(),
        messages: messages,
        timestamp: Date.now(),
        thinkingMode: thinkingMode
      };

      await ipcRenderer.invoke('save-conversation', conversation);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save conversation:', error);
    }
  };

  const generateTitle = () => {
    if (messages.length === 0) return 'New Conversation';
    const firstUserMessage = messages.find(m => m.type === 'user');
    if (firstUserMessage) {
      return firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
    }
    return 'Conversation ' + new Date().toLocaleDateString();
  };

  const startNewConversation = () => {
    if (hasUnsavedChanges && messages.length > 0) {
      saveConversation();
    }
    setMessages([]);
    setConversationId(generateConversationId());
    setConversationTitle('');
    setHasUnsavedChanges(false);
    setMenuAnchor(null);
  };

  const handleSelectConversation = (conversation) => {
    if (hasUnsavedChanges && messages.length > 0) {
      saveConversation();
    }
    
    setMessages(conversation.messages || []);
    setConversationId(conversation.id);
    setConversationTitle(conversation.title);
    setHasUnsavedChanges(false);
  };

  const clearCurrentConversation = () => {
    setMessages([]);
    setConversationId(null);
    setConversationTitle('');
    setHasUnsavedChanges(false);
    setMenuAnchor(null);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || modelStatus !== 'connected') return;

    // Create conversation ID if this is the first message
    if (!conversationId) {
      setConversationId(generateConversationId());
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      thinkingMode
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // This would send to the backend model server
      // For now, simulate a response
      setTimeout(() => {
        const botResponse = {
          id: Date.now() + 1,
          type: 'assistant',
          content: generateResponse(userMessage.content, thinkingMode),
          timestamp: new Date(),
          thinkingMode
        };
        setMessages(prev => [...prev, botResponse]);
        setIsLoading(false);
      }, 1500);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      
      // Show error notification
      if (ipcRenderer) {
        ipcRenderer.invoke('show-notification', {
          title: 'Chat Error',
          body: 'Failed to send message to AI assistant',
          type: 'errors'
        });
      }
    }
  };

  const generateResponse = (input, mode) => {
    const responses = {
      normal: `I understand you're asking about "${input}". Here's my response in normal mode.`,
      thinking: `🤔 **Thinking Process:**
1. Analyzing your question: "${input}"
2. Considering relevant information and context
3. Formulating a comprehensive response

**Response:** Based on my analysis, here's what I think about your question.`,
      research: `📚 **Research-Grade Analysis:**

**Question Analysis:** "${input}"

**Multiple Perspectives:**
1. **Technical Perspective:** Looking at this from a technical standpoint...
2. **Practical Perspective:** In practical terms, this means...
3. **Alternative Viewpoints:** However, one could also argue that...

**Detailed Examination:**
- Key factors to consider
- Potential implications
- Related concepts and connections

**Conclusion:** After thorough analysis, my comprehensive response is...

*Note: This analysis is based on available information and should be verified with authoritative sources.*`
    };
    return responses[mode] || responses.normal;
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h5">
            AI Assistant Chat
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {hasUnsavedChanges && (
              <Tooltip title="Unsaved changes">
                <Chip 
                  label="Unsaved" 
                  color="warning" 
                  size="small"
                  icon={<SaveIcon />}
                />
              </Tooltip>
            )}
            <Tooltip title="Conversation options">
              <IconButton 
                onClick={(e) => setMenuAnchor(e.currentTarget)}
                size="small"
              >
                <MoreVertIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <Chip 
            label={`Mode: ${thinkingMode.charAt(0).toUpperCase() + thinkingMode.slice(1)}`}
            color="primary"
            size="small"
          />
          <Chip 
            label={`Status: ${modelStatus}`}
            color={modelStatus === 'connected' ? 'success' : 'error'}
            size="small"
          />
          {conversationTitle && (
            <Chip 
              label={conversationTitle}
              variant="outlined"
              size="small"
            />
          )}
          {messages.length > 0 && (
            <Chip 
              label={`${messages.length} messages`}
              variant="outlined"
              size="small"
            />
          )}
        </Box>
      </Paper>

      {modelStatus !== 'connected' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please select and start a model in the Model Manager to begin chatting.
        </Alert>
      )}

      <Paper sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {messages.length === 0 ? (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary'
            }}>
              <BotIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                Welcome to your AI Assistant
              </Typography>
              <Typography variant="body2" sx={{ textAlign: 'center', maxWidth: 400 }}>
                Start a conversation by typing a message below. Your conversations will be automatically saved and can be accessed from the history.
              </Typography>
            </Box>
          ) : (
            <List>
              {messages.map((message) => (
                <ListItem key={message.id} sx={{ alignItems: 'flex-start', mb: 2 }}>
                  <Avatar sx={{ mt: 1, mr: 2 }}>
                    {message.type === 'user' ? <PersonIcon /> : <BotIcon />}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      {message.type === 'user' ? 'You' : 'Assistant'}
                      {message.thinkingMode && ` (${message.thinkingMode})`}
                    </Typography>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        mt: 1, 
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {message.content}
                    </Typography>
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                      {message.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Box>
                </ListItem>
              ))}
              {isLoading && (
                <ListItem sx={{ alignItems: 'flex-start' }}>
                  <Avatar sx={{ mt: 1, mr: 2 }}>
                    <BotIcon />
                  </Avatar>
                  <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                    Thinking...
                  </Typography>
                </ListItem>
              )}
            </List>
          )}
          <div ref={messagesEndRef} />
        </Box>

        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={4}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Enter to send, Shift+Enter for new line)"
              disabled={modelStatus !== 'connected' || isLoading}
            />
            <IconButton 
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || modelStatus !== 'connected' || isLoading}
              color="primary"
              size="large"
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Floating Action Button for History */}
      <Fab
        color="primary"
        aria-label="conversation history"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1000
        }}
        onClick={() => setHistoryOpen(true)}
      >
        <HistoryIcon />
      </Fab>

      {/* Conversation Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={startNewConversation}>
          <NewIcon sx={{ mr: 1 }} />
          New Conversation
        </MenuItem>
        <MenuItem onClick={() => { setHistoryOpen(true); setMenuAnchor(null); }}>
          <HistoryIcon sx={{ mr: 1 }} />
          View History
        </MenuItem>
        <MenuItem 
          onClick={() => saveConversation().then(() => setMenuAnchor(null))}
          disabled={!conversationId || messages.length === 0}
        >
          <SaveIcon sx={{ mr: 1 }} />
          Save Conversation
        </MenuItem>
        <MenuItem 
          onClick={clearCurrentConversation}
          disabled={messages.length === 0}
        >
          <ClearIcon sx={{ mr: 1 }} />
          Clear Current Chat
        </MenuItem>
      </Menu>

      {/* Conversation History Dialog */}
      <ConversationHistory
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectConversation={handleSelectConversation}
      />
    </Box>
  );
};

export default ChatInterface;