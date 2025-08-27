# Jihye

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Framework: discord.py](https://img.shields.io/badge/Framework-discord.py-7289DA.svg)](https://github.com/Rapptz/discord.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, minimal Discord bot built with disnake — focused on reliability and ease-of-use for large servers (1k+ members).

✨ Quick highlights

- 🧠 **Autoresponders** — create custom text or embed responses to triggers.
- 🎭 **Reaction Roles** — assign roles when users react to messages.
- ✅ **To‑Do Lists** — per-user to-do list commands.
- 🎧 **Now Playing (Spotify)** — beautiful generated images for Spotify activity.
- ⚙️ **Custom Prefixes** — change the bot prefix per guild.
- 📚 **Interactive Help** — embedded, permission-aware help output.
- 🗄️ **MongoDB-backed** — persistent storage for all features.

---

## 🚀 Quick start

Requirements

- Python 3.8+
- MongoDB
- Discord bot token

Install & run

```bash
git clone https://github.com/ApxllxCartxr/Jihye.git
cd Jihye
pip install -r requirements.txt
```

### Using Docker

Build and run with Docker:

```bash
docker build -t jihye-bot .
docker run -e DISCORD_TOKEN=your_token -e MONGO_URL=your_mongo -e DB_NAME=your_db jihye-bot
```

Or use Docker Compose (includes MongoDB):

```bash
docker-compose up --build
```

Create a `.env` file in the project root with:

```env
DISCORD_TOKEN=your_bot_token_here
MONGO_URL=your_mongodb_connection_string
DB_NAME=your_database_name
```

Run the bot:

```bash
python launcher.py
```

---

## 📖 Usage (quick)

- Default prefix: `?` (can be customized per server)
- `?help` — show command list and details
- `?ar add` / `?ar remove` — manage autoresponders
- `?todo` — manage personal to-do lists

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Please open a PR or an issue on the repository.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

Made with ❤️ — built for communities.
