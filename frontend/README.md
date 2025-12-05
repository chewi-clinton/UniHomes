# CloudDrive - Modern Cloud Storage Frontend

A beautiful, performant, and feature-rich cloud storage web application built with React, Vite, and Tailwind CSS. This frontend connects to a Flask REST API backend to provide a complete cloud storage solution.

## ✨ Features

### 🔐 Authentication
- **Secure OTP-based authentication** - No passwords required
- **Beautiful 6-digit OTP input** with paste support
- **Session management** with automatic token refresh
- **User enrollment** for new users

### 📁 File Management
- **Drag & drop file upload** with progress tracking
- **Multiple file upload** support
- **Folder creation** and navigation
- **Grid and List view** modes
- **File type icons** and previews
- **Context menu** (right-click) for file operations
- **Search functionality** across all files

### 📊 Storage Analytics
- **Storage usage visualization** with interactive charts
- **File type breakdown** with detailed statistics
- **Storage quota monitoring** with visual indicators
- **Recent files** tracking

### 🛠️ Admin Panel
- **Real-time system monitoring** with Server-Sent Events (SSE)
- **User management** interface
- **Storage nodes** health monitoring
- **System events** log with live updates
- **Auto-reconnect** for SSE connections

### 🎨 Design & UX
- **Modern, clean interface** inspired by 2025 design trends
- **Dark mode support** with smooth transitions
- **Responsive design** for all screen sizes
- **Smooth animations** and micro-interactions
- **Loading states** and skeleton screens
- **Toast notifications** for user feedback

### ⌨️ Keyboard Shortcuts
- `↑/↓` - Navigate through files
- `Enter` - Open selected file/folder
- `Delete` - Delete selected file
- `Ctrl/Cmd + F` - Focus search
- `Escape` - Clear selection/close modals

### 🎯 Additional Features
- **Breadcrumb navigation** for easy folder navigation
- **File download** with progress tracking
- **File deletion** with confirmation
- **Empty states** with helpful illustrations
- **Error boundaries** for graceful error handling
- **404 page** with navigation options

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cloud-storage-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

### Build for Production

```bash
npm run build
# or
yarn build
```

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.jsx      # Main app layout with sidebar
│   ├── Header.jsx      # Top navigation header
│   ├── Sidebar.jsx     # Navigation sidebar
│   ├── FileUpload.jsx  # File upload modal with drag & drop
│   ├── ContextMenu.jsx # Right-click context menu
│   └── LoadingSpinner.jsx # Loading states and skeletons
│
├── pages/              # Page components
│   ├── LoginPage.jsx   # Authentication flow
│   ├── DashboardPage.jsx # Main file browser
│   ├── StoragePage.jsx # Storage analytics
│   ├── AdminPage.jsx   # Admin panel
│   └── NotFoundPage.jsx # 404 error page
│
├── contexts/           # React contexts
│   ├── AuthContext.jsx # Authentication state
│   └── ThemeContext.jsx # Dark mode state
│
├── hooks/              # Custom React hooks
│   └── useKeyboardShortcuts.js # Keyboard shortcut handler
│
├── services/           # API services
│   └── api.js          # Axios instance and API methods
│
├── utils/              # Utility functions
│   └── helpers.js      # Formatters and helpers
│
└── index.css           # Global styles and Tailwind config
```

## 🔧 Configuration

### API Base URL
The API base URL is configured in `src/services/api.js`. For development, it uses Vite's proxy configuration in `vite.config.js`:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### Environment Variables
Create a `.env` file in the root directory for environment-specific configuration:

```env
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=CloudDrive
```

## 🎨 Theming

The application supports both light and dark modes with smooth transitions. The theme is managed through the `ThemeContext` and uses CSS custom properties for dynamic theming.

### Adding New Themes
1. Update the color variables in `src/index.css`
2. Extend the theme context in `src/contexts/ThemeContext.jsx`
3. Add theme toggle controls in the UI

## 📱 Responsive Design

The application is fully responsive and optimized for:
- **Desktop** (1200px+)
- **Tablet** (768px - 1199px)
- **Mobile** (< 768px)

Key responsive features:
- Collapsible sidebar on mobile
- Adaptive grid layouts
- Touch-friendly interface elements
- Optimized typography scaling

## 🔒 Security Features

- **Token-based authentication** with Bearer tokens
- **Automatic token refresh** and session management
- **Protected routes** with authentication guards
- **Admin route protection** with role-based access
- **CORS configuration** for API communication

## 🚀 Performance Optimizations

- **Code splitting** with React Router
- **Lazy loading** of components
- **Image optimization** and lazy loading
- **Debounced search** to reduce API calls
- **Virtual scrolling** for large file lists
- **Memoized components** to prevent unnecessary re-renders

## 🧪 Testing

Run the test suite:

```bash
npm test
# or
yarn test
```

### Test Coverage
- Component rendering tests
- Authentication flow tests
- API integration tests
- Keyboard shortcut tests
- Responsive design tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Lucide React** for beautiful icons
- **Tailwind CSS** for utility-first styling
- **Recharts** for interactive charts
- **Sonner** for toast notifications
- **Vite** for fast development and building

## 📞 Support

For support, email support@clouddrive.com or join our Slack channel.

---

**Built with ❤️ by the CloudDrive Team**