import uvicorn
import os

if __name__ == "__main__":
    # Ensure current directory is backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting NetSage AI Troubleshooting Assistant Backend...")
    print("REST API URL: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
