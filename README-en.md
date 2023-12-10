<p align="center">
  <a href="https://github.com/mizhexiaoxiao/vue-fastapi-admin">
    <img alt="Vue FastAPI Admin Logo" width="200" src="https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/logo.svg">
  </a>
</p>

<h1 align="center">vue-fastapi-admin</h1>

English | [简体中文](./README.md)

vue-fastapi-admin is a modern front-end and back-end separation development platform that combines FastAPI, Vue3, and Naive UI. It incorporates RBAC (Role-Based Access Control) management, dynamic routing, and JWT (JSON Web Token) authentication, making it ideal for rapid development of small to medium-sized applications and also serves as a valuable learning resource.

### Features
- **Popular Tech Stack**: The backend is developed with the high-performance asynchronous framework FastAPI using Python 3.11, while the front-end is powered by cutting-edge technologies such as Vue3 and Vite, complemented by the efficient package manager, pnpm.
- **Code Standards**: The project is equipped with various plugins for code standardization and quality control, ensuring consistency and enhancing team collaboration efficiency.
- **Dynamic Routing**: Backend dynamic routing combined with the RBAC model allows for fine-grained control of menus and routing.
- **JWT Authentication**: User identity verification and authorization are handled through JWT, enhancing the application's security.
- **Granular Permission Control**: Implements detailed permission management including button and interface level controls, ensuring different roles and users have appropriate permissions.

### Live Demo
- URL: http://139.9.100.77:9999
- Username: admin
- Password: 123456

### Screenshots

#### Login Page
![Login Page](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/login.jpg)

#### Workbench
![Workbench](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/workbench.jpg)

#### User Management
![User Management](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/user.jpg)

#### Role Management
![Role Management](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/role.jpg)

#### Menu Management
![Menu Management](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/menu.jpg)

#### API Management
![API Management](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/api.jpg)

### Quick Start
Please follow the instructions below for installation and configuration:

#### Method 1：dockerhub pull image

```sh
docker pull mizhexiaoxiao/vue-fastapi-admin:latest 
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 mizhexiaoxiao/vue-fastapi-admin
```

#### Method 2: Build Image Using Dockerfile
##### Install Docker

```sh
yum install -y docker-ce
systemctl start docker
```

##### Build the Image

```sh
git clone https://github.com/mizhexiaoxiao/vue-fastapi-admin.git
cd vue-fastapi-admin
docker build --no-cache . -t vue-fastapi-admin
```

##### Start the Container

```sh
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 vue-fastapi-admin
```

##### Access the Service

http://localhost:9999

username：admin

password：123456

### Local Setup
#### Backend
The backend service requires the following environment:
- Python 3.11
- [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)

1. Create a Python virtual environment:
```sh
poetry shell
```
2. Install project dependencies:
```sh
poetry install
```
3. Start the backend service:
```sh
make run
```
The backend service is now running, and you can visit http://localhost:9999/docs to view the API documentation.

#### Frontend
The frontend project requires a Node.js environment (recommended version 18.8.0 or higher).
- node v18.8.0+

1. Navigate to the frontend project directory:
```sh
cd web
```

2. Install project dependencies (pnpm is recommended: https://pnpm.io/zh/installation)
```sh
npm i -g pnpm # If pnpm is already installed, skip this step
pnpm i # Or use npm i
```

3. Start the frontend development server:
```sh
pnpm dev
```

### Directory Structure Explanation

```
├── app                   // Application directory
│   ├── api               // API interface directory
│   │   └── v1            // Version 1 of the API interfaces
│   │       ├── apis      // API-related interfaces
│   │       ├── base      // Base information interfaces
│   │       ├── menus     // Menu related interfaces
│   │       ├── roles     // Role related interfaces
│   │       └── users     // User related interfaces
│   ├── controllers       // Controllers directory
│   ├── core              // Core functionality module
│   ├── log               // Log directory
│   ├── models            // Data models directory
│   ├── schemas           // Data schema/structure definitions
│   ├── settings          // Configuration settings directory
│   └── utils             // Utilities directory
├── deploy                // Deployment related directory
│   └── sample-picture    // Sample picture directory
└── web                   // Front-end web directory
    ├── build             // Build scripts and configuration directory
    │   ├── config        // Build configurations
    │   ├── plugin        // Build plugins
    │   └── script        // Build scripts
    ├── public            // Public resources directory
    │   └── resource      // Public resource files
    ├── settings          // Front-end project settings
    └── src               // Source code directory
        ├── api           // API interface definitions
        ├── assets        // Static resources directory
        │   ├── images    // Image resources
        │   ├── js        // JavaScript files
        │   └── svg       // SVG vector files
        ├── components    // Components directory
        │   ├── common    // Common components
        │   ├── icon      // Icon components
        │   ├── page      // Page components
        │   ├── query-bar // Query bar components
        │   └── table     // Table components
        ├── composables   // Composable functionalities
        ├── directives    // Directives directory
        ├── layout        // Layout directory
        │   └── components // Layout components
        ├── router        // Routing directory
        │   ├── guard     // Route guards
        │   └── routes    // Route definitions
        ├── store         // State management (pinia)
        │   └── modules   // State modules
        ├── styles        // Style files directory
        ├── utils         // Utilities directory
        │   ├── auth      // Authentication related utilities
        │   ├── common    // Common utilities
        │   ├── http      // Encapsulated axios
        │   └── storage   // Encapsulated localStorage and sessionStorage
        └── views         // Views/Pages directory
            ├── error-page // Error pages
            ├── login      // Login page
            ├── profile    // Profile page
            ├── system     // System management page
            └── workbench  // Workbench page
```

### Visitors Count

<img align="left" src = "https://profile-counter.glitch.me/vue-fastapi-admin/count.svg" alt="Loading">