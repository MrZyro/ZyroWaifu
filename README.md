<h1 align="center"><b>🌸 Waifu & Husbando Catcher Bot 🌸</b></h1> 

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="Divider">
</p>

<p align="center">
  <img src="https://files.catbox.moe/gknnju.jpg" alt="Waifu Bot Poster" width="600" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
</p>

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" alt="Divider">
</p>

<p align="center">
  <b>A feature-rich Telegram Bot for catching, guessing, and trading anime characters, with interactive games (Blackjack, Mines, Chess, Tic-Tac-Toe) and web dashboard support.</b>
</p>

<p align="center">
  <a href="https://dashboard.heroku.com/new?template=https://github.com/MrZyro/ZyroWaifu">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku" height="40">
  </a>
</p>

<p align="center">
  <a href="https://t.me/MrZyro_dev">
    <img src="https://img.shields.io/badge/Developer-Telegram-blue?style=for-the-badge&logo=telegram" alt="Developer Telegram">
  </a>
  &nbsp;
  <a href="https://github.com/MrZyro">
    <img src="https://img.shields.io/badge/GitHub-Profile-black?style=for-the-badge&logo=github" alt="GitHub Profile">
  </a>
</p>

---

## 🛠️ Features

* **Character Spawning**: Random anime characters spawn in group chats based on message activity.
* **Catching / Guessing**: Collect characters by guessing their names.
* **Casino Games**: Blackjack, Minesweeper, Coinflip, Slots, Higher-or-Lower, and Wheel of Fortune.
* **Multiplayer Games**: Real-time Chess (via Mini-App) and Tic-Tac-Toe betting lobbies.
* **Economy System**: Balances and payments.
* **Wanted Poster**: Custom One Piece style bounty poster generator.

---

## 🚀 Hosting Guide

### Option 1: VPS Deployment (Virtual Private Server)

#### 1. System Prerequisites
Ensure your VPS has Python, Node.js, and Git installed.
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Git, Python3, and pip
sudo apt install -y git python3 python3-pip

# Install Node.js (v18.x recommended)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Clone the Repository
```bash
git clone https://github.com/MrZyro/WaifuBot.git
cd WaifuBot
```

#### 3. Install Dependencies
```bash
# Install Python packages
pip3 install -r requirements.txt

# Install Node.js packages
npm install
```

#### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
nano .env
```
Fill in the `API_ID`, `API_HASH`, `TOKEN`, `MONGO_URL`, and other settings.

#### 5. Daemonizing (Running in background)
To keep the bot running 24/7, we recommend using **PM2** (Process Manager 2):
```bash
# Install PM2 globally
sudo npm install -p pm2 -g

# Start the Python bot
pm2 start "python3 -m TEAMZYRO" --name "waifu-python"

# Start the Node.js bot (for WebApps/Inline)
pm2 start bot.js --name "waifu-node"

# Save process list to persist on reboot
pm2 save
pm2 startup
```

---

### Option 2: Docker Deployment

If you prefer containerized deployment:
```bash
# Build the Docker image
docker build -t waifubot .

# Run the container
docker run -d --env-file .env --name waifubot-container waifubot
```

---

### Option 3: Heroku Deployment

Simply click the deployment button below, fill out the environment variables in the Heroku dashboard, and click deploy:

<p align="center">
  <a href="https://dashboard.heroku.com/new?template=https://github.com/MrZyro/ZyroWaifu">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku" height="45">
  </a>
</p>

---

## 📄 License
This repository is licensed under the [MIT License](file:///h:/myprojet/NEWONE/WaifuBot/LICENSE).
