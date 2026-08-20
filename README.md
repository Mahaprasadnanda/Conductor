<div align="center">
  <h1>🚀 Conductor</h1>
  <p><strong>The Developer-First, High-Performance API Gateway</strong></p>
  <p>
    Built for modern microservices to route, monitor, secure, and analyze traffic with zero friction.
  </p>
</div>

---

## 🌟 Overview

**Conductor** is an open-source API Gateway and Management platform built from the ground up for performance and developer experience. It acts as the single entry point for all your microservices, providing out-of-the-box routing, rate limiting, authentication, and deep traffic analytics.

Whether you're running a small hobby project or a fleet of distributed microservices, Conductor simplifies your network edge.

## ✨ Features

- **⚡ Blazing Fast Routing:** Built on top of FastAPI and async I/O to ensure minimal latency overhead during proxying.
- **🛡️ Secure by Default:** Built-in JWT authentication, API Key management, and CORS controls.
- **🚦 Traffic Control:** Granular, Redis-backed rate limiting and active health checking to ensure upstream resilience.
- **📊 Deep Analytics & Metrics:** Natively exports metrics to Prometheus and Grafana Cloud (via Grafana Alloy) for real-time observability.
- **🏢 Multi-Tenant Isolation:** Organize your services cleanly into Projects, ensuring strict logical boundaries.
- **💻 Beautiful UI:** A fully-featured modern React/Vite dashboard to manage services, view analytics, and generate API keys.

## 🏗️ Architecture

Conductor consists of two primary components:
1. \ackend/\: A high-performance Python **FastAPI** application backed by **PostgreSQL** (metadata & configuration) and **Redis** (caching, rate limiting).
2. \rontend/\: A sleek, responsive **React + Vite** dashboard utilizing Tailwind CSS and Recharts.

---

## 🚀 Quick Start (Local Development)

The easiest way to run Conductor locally is using Docker Compose.

### Prerequisites
- Docker & Docker Compose
- Node.js (for local frontend development)
- Python 3.13 (for local backend development)

### 1. Clone the repository
\\\ash
git clone https://github.com/Mahaprasadnanda/Conductor.git
cd Conductor
\\\

### 2. Run with Docker Compose
We provide a fully configured \docker-compose.yml\ that spins up the Frontend, Backend, PostgreSQL, Redis, and a local Prometheus instance.

\\\ash
docker compose up -d
\\\

- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus UI:** [http://localhost:9090](http://localhost:9090)

---

## 🌐 Production Deployment

Conductor is designed to be easily deployed to modern cloud providers like Render, Vercel, and Neon.

### Backend (Render + Neon Postgres + Upstash Redis)
1. Provision a free PostgreSQL database on [Neon.tech](https://neon.tech).
2. Provision a free Redis instance on [Upstash](https://upstash.com).
3. Connect your GitHub repository to a **Render Web Service**.
4. Set the Root Directory to \ackend\.
5. Set the required environment variables:
   - \DATABASE_URL\ (e.g., \postgresql+asyncpg://...\)
   - \REDIS_URL\
   - \JWT_SECRET_KEY\
   - \CORS_ORIGINS\ (Point to your frontend URL)
6. Conductor will automatically run database migrations on boot via \start.sh\.

### Frontend (Vercel)
1. Connect your repository to **Vercel**.
2. Set the Root Directory to \rontend\.
3. Framework Preset: **Vite**.
4. Add the \VITE_API_URL\ environment variable pointing to your deployed backend.
5. Deploy!

---

## 🤝 Contributing

**Contributions are highly welcome and deeply appreciated!** 

If you have suggestions for improvements, want to fix a bug, or want to add a new feature:
1. Fork the Project
2. Create your Feature Branch (\git checkout -b feature/AmazingFeature\)
3. Commit your Changes (\git commit -m 'Add some AmazingFeature'\)
4. Push to the Branch (\git push origin feature/AmazingFeature\)
5. Open a Pull Request

## 📬 Contact & Support

For queries, suggestions, or support, please reach out!

📧 **Email:** [Mahaprasad.programmer@gmail.com](mailto:Mahaprasad.programmer@gmail.com)  
🐙 **GitHub:** [Mahaprasadnanda](https://github.com/Mahaprasadnanda)

---
<div align="center">
  <p>Built with ❤️ for developers.</p>
</div>
