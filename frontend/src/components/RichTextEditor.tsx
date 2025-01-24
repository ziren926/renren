import React, { useRef } from 'react';
import { Editor } from '@tinymce/tinymce-react';
import type { Editor as TinyMCEEditorType } from 'tinymce';
import api from '../config/axios';
import './RichTextEditor.css'; // 我们稍后会创建这个样式文件

interface RichTextEditorProps {
  initialValue?: string;
  onChange: (content: string) => void;
  token: string;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ initialValue = '', onChange, token }) => {
  const editorRef = useRef<TinyMCEEditorType | null>(null);

  const handleImageUpload = async (blobInfo: any): Promise<string> => {
    const formData = new FormData();
    formData.append('file', blobInfo.blob(), blobInfo.filename());

    try {
      console.log('Uploading image...'); // 调试日志
      const response = await api.post('/api/posts/upload-image', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        }
      });

      console.log('Upload response:', response.data); // 调试日志

      if (response.data.success) {
        // 使用后端返回的完整URL
        const imageUrl = `http://localhost:5000${response.data.data.url}`; // 确保这里的端口号与后端一致
        console.log('Final image URL:', imageUrl); // 调试日志
        return imageUrl;
      }
      throw new Error(response.data.message || '图片上传失败');
    } catch (error: any) {
      console.error('Image upload error:', error);
      console.error('Error details:', error.response?.data); // 调试日志
      throw new Error(error.response?.data?.message || '图片上传失败');
    }
  };

  return (
    <div className="rich-text-editor">
      <Editor
        id="tiny-react"
        tinymceScriptSrc={`${process.env.PUBLIC_URL}/tinymce/tinymce.min.js`}
        onInit={(evt, editor) => {
          editorRef.current = editor;
        }}
        initialValue={initialValue}
        init={{
          height: 500,
          menubar: true,
          plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'code', 'help', 'wordcount'
          ],
          toolbar: 'undo redo | formatselect | ' +
            'bold italic backcolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | ' +
            'removeformat | image media | help',
          content_style: `
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
              font-size: 16px;
              line-height: 1.6;
              color: #333;
              max-width: 900px;
              margin: 0 auto;
              padding: 20px;
            }
            img {
              max-width: 100%;
              height: auto;
            }
          `,
          branding: false,
          language: 'zh_CN',
          images_upload_handler: handleImageUpload,
          automatic_uploads: true,
          file_picker_types: 'image',
          paste_data_images: true,
          image_title: true,
          image_caption: true,
          image_dimensions: false,
          image_class_list: [
            { title: '默认', value: '' },
            { title: '响应式', value: 'img-fluid' }
          ],
          image_advtab: true,
          image_uploadtab: true,
          file_picker_callback: function(callback, value, meta) {
            const input = document.createElement('input');
            input.setAttribute('type', 'file');
            input.setAttribute('accept', 'image/*');
            
            input.onchange = async function() {
              const file = (input as HTMLInputElement).files?.[0];
              if (!file) return;

              try {
                // 直接使用 handleImageUpload 上传图片
                const formData = new FormData();
                formData.append('file', file);

                const response = await api.post('/api/posts/upload-image', formData, {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data',
                  }
                });

                if (response.data.success) {
                  callback(response.data.data.url, { 
                    title: file.name,
                    alt: file.name 
                  });
                } else {
                  throw new Error(response.data.message || '图片上传失败');
                }
              } catch (error: any) {
                console.error('Image upload error:', error);
                // 如果编辑器实例存在，显示错误消息
                if (editorRef.current) {
                  editorRef.current.notificationManager.open({
                    text: error.message || '图片上传失败',
                    type: 'error',
                    timeout: 3000
                  });
                }
              }
            };

            input.click();
          },
          setup: (editor) => {
            editor.on('Change', () => {
              onChange(editor.getContent());
            });
            
            // 添加图片上传成功的提示
            editor.on('ImageUploadSuccess', (e) => {
              editor.notificationManager.open({
                text: '图片上传成功',
                type: 'success',
                timeout: 2000
              });
            });
            
            // 添加图片上传失败的提示
            editor.on('ImageUploadError', (e) => {
              editor.notificationManager.open({
                text: '图片上传失败',
                type: 'error',
                timeout: 3000
              });
            });
          }
        }}
      />
    </div>
  );
};

export default RichTextEditor; 