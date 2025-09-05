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
  Alert
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon
} from '@mui/icons-material';

const ChatInterface = ({ thinkingMode, modelStatus }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || modelStatus !== 'connected') return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
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
          content: generateResponse(inputValue, thinkingMode),
          timestamp: new Date(),
          thinkingMode
        };
        setMessages(prev => [...prev, botResponse]);
        setIsLoading(false);
      }, 1500);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
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
        <Typography variant="h5" gutterBottom>
          AI Assistant Chat
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
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
        </Box>
      </Paper>

      {modelStatus !== 'connected' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please select and start a model in the Model Manager to begin chatting.
        </Alert>
      )}

      <Paper sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
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
          <div ref={messagesEndRef} />
        </Box>

        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={modelStatus !== 'connected' || isLoading}
            />
            <IconButton 
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || modelStatus !== 'connected' || isLoading}
              color="primary"
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatInterface;