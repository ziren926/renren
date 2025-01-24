import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import RichTextEditor from './RichTextEditor';
import { useAuth } from '../contexts/AuthContext';
import './CreatePost.css';

interface DraftPost {
  title: string;
  content: string;
  lastSaved?: Date;
}

const CreatePost: React.FC = () => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [draftId, setDraftId] = useState<string | null>(null);
  const navigate = useNavigate();
  const { token, isAuthenticated } = useAuth();

  // 如果用户未登录，重定向到登录页面
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/posts/create' } });
    }
  }, [isAuthenticated, navigate]);

  // 加载草稿
  useEffect(() => {
    const loadDraft = async () => {
      try {
        const response = await axios.get('/api/posts/drafts/latest', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.data.success && response.data.data) {
          const draft = response.data.data;
          setTitle(draft.title);
          setContent(draft.content);
          setDraftId(draft._id);
          setLastSaved(new Date(draft.updatedAt));
        }
      } catch (error) {
        console.error('Failed to load draft:', error);
      }
    };

    loadDraft();
  }, [token]);

  // 自动保存功能
  const saveDraft = useCallback(async () => {
    if (!title && !content) return;
    
    setIsSaving(true);
    try {
      const endpoint = draftId 
        ? `/api/posts/drafts/${draftId}` 
        : '/api/posts/drafts';
      
      const method = draftId ? 'put' : 'post';
      
      const response = await axios({
        method,
        url: endpoint,
        data: { title, content },
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        setLastSaved(new Date());
        if (!draftId) {
          setDraftId(response.data.data._id);
        }
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsSaving(false);
    }
  }, [title, content, draftId, token]);

  // 自动保存定时器
  useEffect(() => {
    const timer = setTimeout(saveDraft, 3000);
    return () => clearTimeout(timer);
  }, [title, content, saveDraft]);

  // 发布文档
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const response = await axios.post('/api/posts', {
        title,
        content,
        contentType: 'richtext',
        draftId // 如果是从草稿发布，传递草稿ID
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        // 发布成功后删除草稿
        if (draftId) {
          await axios.delete(`/api/posts/drafts/${draftId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
        }
        navigate(`/posts/${response.data.data.postId}`);
      } else {
        setError(response.data.message || '创建文档失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '创建文档失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 如果用户未登录，不渲染内容
  if (!isAuthenticated || !token) {
    return null;
  }

  return (
    <div className="create-post-container">
      <div className="create-post-header">
        <h2>创建新文档</h2>
        <div className="post-actions">
          <button
            className={`preview-button ${isPreviewMode ? 'active' : ''}`}
            onClick={() => setIsPreviewMode(!isPreviewMode)}
          >
            {isPreviewMode ? '编辑' : '预览'}
          </button>
          <div className="save-status">
            {isSaving ? '保存中...' : 
             lastSaved ? `上次保存: ${lastSaved.toLocaleTimeString()}` : 
             ''}
          </div>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit} className="create-post-form">
        <div className="form-group">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="输入标题..."
            className="title-input"
            required
          />
        </div>

        <div className="form-group">
          {isPreviewMode ? (
            <div className="preview-content">
              <h1>{title}</h1>
              <div dangerouslySetInnerHTML={{ __html: content }} />
            </div>
          ) : (
            <RichTextEditor
              initialValue={content}
              onChange={setContent}
              token={token}
            />
          )}
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className="submit-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? '发布中...' : '发布文档'}
          </button>
          <button 
            type="button" 
            className="save-draft-button"
            onClick={saveDraft}
            disabled={isSaving}
          >
            {isSaving ? '保存中...' : '保存草稿'}
          </button>
          <button 
            type="button" 
            className="cancel-button"
            onClick={() => navigate(-1)}
            disabled={isSubmitting || isSaving}
          >
            取消
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreatePost; 