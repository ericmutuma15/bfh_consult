# BFH Consult - Full Stack Medical Consultation App

## Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. (First time) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at http://localhost:8000

## Frontend (React Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The app will be available at the URL shown in the terminal (usually http://localhost:5173).

## Android Deployment

- To deploy the web frontend as an Android app, use a tool like [Capacitor](https://capacitorjs.com/) or [Cordova](https://cordova.apache.org/) to wrap the React app in a WebView.
- Example (with Capacitor):
  1. In the frontend directory, run:
     ```bash
     npm install @capacitor/core @capacitor/cli
     npx cap init
     npx cap add android
     npm run build
     npx cap copy android
     npx cap open android
     ```
  2. Open the project in Android Studio and build/run on a device or emulator.

## Notes
- The backend uses in-memory storage for demo purposes. For production, connect to a real database.
- The Daraja (M-Pesa) payment endpoint is a stub. Integrate with Safaricom's API for real payments.
- Update environment variables and secrets as needed for production.
