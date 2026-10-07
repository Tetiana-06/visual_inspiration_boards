import os
import sys
import uvicorn

if __name__ == "__main__":
    # За замовчуванням 8000, але можна передати як аргумент (python main.py 8080) або через PORT в .env
    port = int(os.getenv("PORT", 8000))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
        
    print(f"🚀 Запуск сервера на порту {port} -> http://localhost:{port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
