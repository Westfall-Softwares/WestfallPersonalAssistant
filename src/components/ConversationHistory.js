import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  TextField,
  Typography,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Fab,
  InputAdornment,
  Divider,
  Paper,
  Menu,
  MenuItem,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  Chat as ChatIcon,
  MoreVert as MoreVertIcon,
  Restore as RestoreIcon,
  Archive as ArchiveIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon
} from '@mui/icons-material';

const { ipcRenderer } = window.electronAPI;

function ConversationHistory({ open, onClose, onSelectConversation }) {
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredConversations, setFilteredConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedConversationId, setSelectedConversationId] = useState(null);

  useEffect(() => {
    if (open) {
      loadConversations();
    }
  }, [open]);

  useEffect(() => {
    filterConversations();
  }, [conversations, searchQuery]);

  const loadConversations = async () => {
    try {
      const result = await ipcRenderer.invoke('get-conversations');
      // Sort by timestamp, most recent first
      const sorted = result.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setConversations(sorted);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const filterConversations = async () => {
    if (!searchQuery.trim()) {
      setFilteredConversations(conversations);
      return;
    }

    try {
      const results = await ipcRenderer.invoke('search-conversations', searchQuery);
      setFilteredConversations(results);
    } catch (error) {
      console.error('Search failed:', error);
      // Fallback to local filtering
      const filtered = conversations.filter(conv =>
        conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.messages?.some(msg =>
          msg.content?.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
      setFilteredConversations(filtered);
    }
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      await ipcRenderer.invoke('delete-conversation', conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));
      setDeleteDialogOpen(false);
      setSelectedConversationId(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleRestoreConversation = (conversation) => {
    onSelectConversation(conversation);
    onClose();
  };

  const handleMenuClick = (event, conversationId) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedConversationId(conversationId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedConversationId(null);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = (now - date) / (1000 * 60 * 60);

    if (diffHours < 1) {
      return 'Just now';
    } else if (diffHours < 24) {
      return `${Math.floor(diffHours)} hours ago`;
    } else if (diffHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  const getMessagePreview = (messages) => {
    if (!messages || messages.length === 0) return 'No messages';
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content?.substring(0, 100) + (lastMessage.content?.length > 100 ? '...' : '');
  };

  const getThinkingModeChip = (conversation) => {
    const modes = new Set();
    conversation.messages?.forEach(msg => {
      if (msg.thinkingMode) modes.add(msg.thinkingMode);
    });

    if (modes.has('research')) return <Chip label="Research" size="small" color="secondary" />;
    if (modes.has('thinking')) return <Chip label="Thinking" size="small" color="primary" />;
    return <Chip label="Normal" size="small" variant="outlined" />;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <HistoryIcon />
        <Typography variant="h6">Conversation History</Typography>
        <Chip 
          label={`${filteredConversations.length} conversations`} 
          size="small" 
          variant="outlined" 
        />
      </DialogTitle>

      <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
        <Box sx={{ p: 2 }}>
          <TextField
            fullWidth
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            size="small"
          />
        </Box>

        <Divider />

        <Box sx={{ flex: 1, overflow: 'auto' }}>
          {filteredConversations.length === 0 ? (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary'
            }}>
              <ChatIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6">
                {searchQuery ? 'No conversations found' : 'No conversations yet'}
              </Typography>
              <Typography variant="body2">
                {searchQuery ? 'Try a different search term' : 'Start chatting to see your conversation history'}
              </Typography>
            </Box>
          ) : (
            <List>
              {filteredConversations.map((conversation, index) => (
                <React.Fragment key={conversation.id}>
                  <ListItem 
                    sx={{ 
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                    onClick={() => handleRestoreConversation(conversation)}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle1" sx={{ flex: 1 }}>
                            {conversation.title || `Conversation ${conversation.id?.substring(0, 8) || index + 1}`}
                          </Typography>
                          {getThinkingModeChip(conversation)}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                            {getMessagePreview(conversation.messages)}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="caption" color="text.secondary">
                              {formatTimestamp(conversation.timestamp)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {conversation.messages?.length || 0} messages
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title="Options">
                        <IconButton
                          edge="end"
                          onClick={(e) => handleMenuClick(e, conversation.id)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < filteredConversations.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button 
          variant="outlined" 
          onClick={loadConversations}
          startIcon={<RestoreIcon />}
        >
          Refresh
        </Button>
      </DialogActions>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem 
          onClick={() => {
            const conversation = conversations.find(c => c.id === selectedConversationId);
            if (conversation) handleRestoreConversation(conversation);
            handleMenuClose();
          }}
        >
          <RestoreIcon sx={{ mr: 1 }} />
          Restore Conversation
        </MenuItem>
        <MenuItem 
          onClick={() => {
            setDeleteDialogOpen(true);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Conversation
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Conversation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this conversation? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => handleDeleteConversation(selectedConversationId)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}

export default ConversationHistory;