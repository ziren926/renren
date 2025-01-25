from app import mongo, ckeditor  # 添加 ckeditor 导入

@bp.route('/market')
def index():
    # ... 其他代码保持不变 ...
    return render_template('market/index.html', demands=demands, 
                         hot_demands=hot_demands, recent_demands=recent_demands, 
                         ckeditor=ckeditor)  # 传递 ckeditor 到模板 