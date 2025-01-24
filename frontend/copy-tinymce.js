const fs = require('fs-extra');
const path = require('path');

const source = path.join(__dirname, 'node_modules', 'tinymce');
const destination = path.join(__dirname, 'public', 'tinymce');

// 确保目标目录存在
fs.ensureDirSync(destination);

// 复制文件
fs.copySync(source, destination, {
    filter: (src) => {
        return !src.includes('node_modules') && !src.includes('.git');
    }
});

console.log('TinyMCE files copied successfully!'); 