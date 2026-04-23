<div align="center">

<!-- Animated Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=StudX&fontSize=80&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Smart%20School%20Management%20System&descAlignY=60&descSize=22" width="100%"/>

<!-- Animated Typing -->
<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=6E57F7&center=true&vCenter=true&random=false&width=600&lines=Welcome+to+StudX+%F0%9F%8E%93;Built+with+Python+%2B+Django+%F0%9F%90%8D;Manage+Students%2C+Teachers+%26+Staff;Open+Source+%26+Community+Driven+%F0%9F%9A%80" alt="Typing SVG" />
</a>

<br/><br/>

<!-- Badges Row 1 -->
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-Framework-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-Open%20Source-green?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=for-the-badge&logo=githubactions&logoColor=white)]()

<br/>

<!-- Badges Row 2 -->

</div>

---

## 🌟 What is StudX?

> **StudX** is a modern, web-based **School Management System** built with Python and Django. It simplifies the complex day-to-day operations of educational institutions — from managing students and teachers to handling staff records — all in one place.

<div align="center">
  <img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="400"/>
</div>

---

## 📋 Table of Contents

<div align="center">

| Section | Link |
|---|---|
| 🚀 Features | [View Features](#-features) |
| 🛠️ Tech Stack | [View Stack](#️-tech-stack) |
| ⚡ Quick Start | [Get Started](#-quick-start) |
| 📁 Project Structure | [View Structure](#-project-structure) |
| 🤝 Contributing | [Contribute](#-contributing) |
| 📄 License | [License](#-license) |

</div>

---

## 🚀 Features

<div align="center">
  <img src="https://user-images.githubusercontent.com/74038190/216122065-2f028bae-25d6-4a3c-bc9f-175394ed5011.png" width="50" />
</div>

<table>
  <tr>
    <td>👨‍🎓 <b>Student Management</b></td>
    <td>Register, update & track all student records</td>
  </tr>
  <tr>
    <td>👩‍🏫 <b>Teacher Management</b></td>
    <td>Maintain teacher profiles, subjects & schedules</td>
  </tr>
  <tr>
    <td>🏢 <b>Staff Management</b></td>
    <td>Handle non-teaching staff information easily</td>
  </tr>
  <tr>
    <td>📊 <b>Dashboard & Reports</b></td>
    <td>Get a bird's-eye view of all school operations</td>
  </tr>
  <tr>
    <td>🔐 <b>Role-based Access</b></td>
    <td>Different permissions for admin, teachers & staff</td>
  </tr>
  <tr>
    <td>📱 <b>Responsive Design</b></td>
    <td>Works seamlessly across devices</td>
  </tr>
</table>

---

## 🛠️ Tech Stack

<div align="center">

[![Python](https://skillicons.dev/icons?i=python)](https://python.org)
[![Django](https://skillicons.dev/icons?i=django)](https://djangoproject.com)
[![HTML](https://skillicons.dev/icons?i=html)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS](https://skillicons.dev/icons?i=css)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://skillicons.dev/icons?i=js)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![SQLite](https://skillicons.dev/icons?i=sqlite)](https://sqlite.org)
[![Git](https://skillicons.dev/icons?i=git)](https://git-scm.com)
[![GitHub](https://skillicons.dev/icons?i=github)](https://github.com)

</div>

| Technology | Purpose |
|---|---|
| **Python 3.x** | Core programming language |
| **Django** | Web framework & ORM |
| **SQLite / PostgreSQL** | Database |
| **HTML/CSS/JS** | Frontend templating |
| **Virtualenv** | Dependency isolation |

---

## ⚡ Quick Start

### Prerequisites

Make sure you have the following installed:

- ![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white) — [Download](https://python.org)
- ![pip](https://img.shields.io/badge/pip-latest-orange?logo=pypi&logoColor=white)
- ![Git](https://img.shields.io/badge/Git-installed-red?logo=git&logoColor=white) — [Download](https://git-scm.com)

---

### 🔧 Installation

**1. Clone the repository**
```bash
git clone https://github.com/jashchothani/StudX.git
cd StudX
```

**2. Create & activate a virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**5. Create a superuser (Admin)**
```bash
python manage.py createsuperuser
```

**6. Start the server 🚀**
```bash
python manage.py runserver
```

> Open your browser and visit: **[https://studx-1cub.onrender.com/login](https://studx-1cub.onrender.com/login)**

---

## 📁 Project Structure

```
📁 StudX/
│
├── 📁 static/
│   ├── 📁 faces/                🤖 (AI face data)
│   ├── 🎨 portal.css
│   ├── ⚡ portal.js
│   ├── ⚡ student.js
│   └── 🎨 styles.css
│
├── 📁 templates/
│   ├── 🌐 admin_dashboard.html
│   ├── 🌐 base.html
│   ├── 🌐 base2.html
│   ├── 🌐 features.html
│   ├── 🌐 index.html
│   ├── 🌐 login.html
│   ├── 🌐 parent_dashboard.html
│   ├── 🌐 register.html
│   ├── 🌐 student_dashboard.html
│   ├── 🌐 teacher_dashboard.html
│   ├── 🌐 timetable.html
│   └── 🌐 verify_otp.html
│
├── ⚙️ .gitignore
├── 📘 README.md
├── 🐍 app.py
├── 📦 requirements.txt
├── 🗄️ studx.db
├── 🗄️ studx.db-journal
├── 🐍 table.py
├── 🤖 train_faces.py
└── 🤖 trainer.yml

```

---

## 🗺️ Roadmap

- [x] Student Management Module
- [x] Teacher Management Module
- [x] Staff Management Module
- [ ] Attendance Tracking System
- [ ] Grades & Result Management
- [ ] Parent Portal
- [ ] Notification System
- [ ] API Support (REST)
- [ ] Docker Support

---

## 🤝 Contributing

Contributions are always welcome! Here's how you can help:

<div align="center">

[![Fork](https://img.shields.io/badge/1.%20Fork-the%20repo-blue?style=for-the-badge&logo=github)](https://github.com/jashchothani/StudX/fork)
[![Branch](https://img.shields.io/badge/2.%20Create-a%20branch-green?style=for-the-badge&logo=git)](https://github.com/jashchothani/StudX)
[![Commit](https://img.shields.io/badge/3.%20Commit-your%20changes-orange?style=for-the-badge&logo=githubactions)](https://github.com/jashchothani/StudX)
[![PR](https://img.shields.io/badge/4.%20Open-a%20Pull%20Request-purple?style=for-the-badge&logo=github)](https://github.com/jashchothani/StudX/pulls)

</div>

```bash
# Create your feature branch
git checkout -b feature/AmazingFeature

# Commit your changes
git commit -m "Add some AmazingFeature"

# Push to the branch
git push origin feature/AmazingFeature

# Open a Pull Request 🎉
```

> 💡 Found a bug? Have a suggestion? [Open an issue](https://github.com/jashchothani/StudX/issues)!


---

## 👨‍💻 Author

<div align="center">

<a href="https://github.com/jashchothani">
  <img src="https://avatars.githubusercontent.com/jashchothani" width="80" style="border-radius:50%"/>
</a>

[![GitHub](https://img.shields.io/badge/GitHub-jashchothani-181717?style=for-the-badge&logo=github)](https://github.com/jashchothani)
</div>

---

## 📄 License

This project is **open source** and available to the community. Frameworks, packages, and libraries used are under their own respective licenses.

---

## 🌟 Show Your Support

If this project helped you or you find it useful, please consider giving it a ⭐ star — it means a lot!

<div align="center">

[![Star this repo](https://img.shields.io/badge/⭐%20Star%20this%20repo-it%20helps!-yellow?style=for-the-badge)](https://github.com/jashchothani/StudX/stargazers)

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer&animation=twinkling" width="100%"/>

</div>

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/jashchothani">Jash Chothani</a></sub>
</div>
