import React, { useState, useEffect } from 'react';
import RichTextEditor from './RichTextEditor';
import axios from 'axios';

interface PostEditorProps {
  postId?: string;
  token: string;
}

const PostEditor: React.FC<PostEditorProps> = ({ postId, token }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // 加载帖子内容
  useEffect(() => {
    if (postId) {
      loadPost();
    }
  }, [postId]);

  // 自动保存
  useEffect(() => {
    const timer = setTimeout(() => {
      if (title || content) {
        savePost();
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [title, content]);

  const loadPost = async () => {
    try {
      const response = await axios.get(`/api/posts/${postId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTitle(response.data.data.title);
      setContent(response.data.data.content);
    } catch (error) {
      console.error('Load post error:', error);
    }
  };

  const savePost = async () => {
    if (saving) return;

    try {
      setSaving(true);
      const method = postId ? 'put' : 'post';
      const url = postId ? `/api/posts/${postId}` : '/api/posts';

      const response = await axios({
        method,
        url,
        data: { title, content },
        headers: { Authorization: `Bearer ${token}` }
      });

      setLastSaved(new Date());
      if (!postId) {
        // 如果是新帖子，更新 URL
        window.history.replaceState(
          null, 
          '', 
          `/posts/edit/${response.data.data.postId}`
        );
      }
    } catch (error) {
      console.error('Save post error:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="post-editor">
      <div className="editor-header">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="输入标题..."
          className="title-input"
        />
        <div className="save-status">
          {saving ? '保存中...' : 
           lastSaved ? `上次保存: ${lastSaved.toLocaleTimeString()}` : 
           ''}
        </div>
      </div>
      
      <RichTextEditor
        initialValue={content}
        onChange={setContent}
        token={token}
      />

      <div className="editor-footer">
        <button 
          onClick={savePost}
          disabled={saving}
          className="save-button"
        >
          {saving ? '保存中...' : '保存'}
        </button>
      </div>
    </div>
  );
};

export default PostEditor; 