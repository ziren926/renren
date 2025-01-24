from app import create_app

app = create_app()

if __name__ == '__main__':
    # 禁用 reloader 来避免 socket 错误
    app.run(debug=True, use_reloader=False) 