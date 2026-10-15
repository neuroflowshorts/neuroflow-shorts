# NeuroFlow Shorts Bot (100% free)

Makes and uploads one YouTube Short per day for the NeuroFlow channel (gentle productivity for ADHD / autistic / anxious brains).
Runs in the cloud on GitHub Actions, so your computer can stay off after setup.

**Pipeline:** topic (topics.csv) -> Gemini writes script -> edge-tts voice -> Pexels stock clips -> ffmpeg adds captions + music -> YouTube upload.

## One-time setup (about 1 to 2 hours)

### 1. Free API keys
- **Gemini:** https://aistudio.google.com/apikey -> Create API key (no card needed).
- **Pixabay (stock videos):** sign up free at https://pixabay.com, then open https://pixabay.com/api/docs/ while logged in. Your key is shown in the text there. (Pexels also works, but it has paused new keys. Skip it.)
- Without any video key the bot still works, with a plain dark background.

### 2. YouTube upload access (Google Cloud, no billing needed)
1. Go to https://console.cloud.google.com and create a project.
2. APIs & Services -> Library -> enable **YouTube Data API v3**.
3. APIs & Services -> **OAuth consent screen** -> External -> fill app name and your email.
4. Add yourself as a test user, then click **Publish app** so the status becomes **In production**.
   IMPORTANT: if you leave it in "Testing", the token expires after 7 days and the bot stops.
   (Google will show an "unverified app" warning when you log in. That is fine for your own channel: Advanced -> Continue.)
5. Credentials -> Create credentials -> **OAuth client ID** -> Application type **Desktop app** -> Download JSON.
   Rename it `client_secret.json` and put it next to `get_token.py`.
6. On your computer (Python installed): `pip install google-auth-oauthlib` then `python get_token.py`.
   Log in with the Google account that owns NeuroFlow. It prints 3 values. Copy them.

### 3. GitHub
1. Create a free account and a new repository (public is best: unlimited free Actions minutes).
2. Upload all files from this folder (keep the `.github/workflows/daily.yml` path).
3. Repo -> Settings -> Secrets and variables -> Actions -> **New repository secret**. Add:
   `GEMINI_API_KEY`, `PIXABAY_API_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`
4. (Optional) Variables tab -> New variable `PRIVACY` = `private` or `public` (default is private).
   Keep your secrets secret. Never put them in code or in a public post.

### 4. Test it
Actions tab -> "Daily NeuroFlow Short" -> **Run workflow**. After ~5 minutes:
- Download the `short` artifact to preview the video, and
- open YouTube Studio to see the upload.

## Daily routine (2 minutes)
- Start in **private** mode. Open YouTube Studio on your phone, watch the Short, and press Publish if it is good.
- After about 2 weeks of good results, you may set `PRIVACY=public` for hands-off posting. Still skim the channel weekly.

## Known limits
- New API projects may force uploads to private until Google approves your project (the "YouTube API Services audit"). Until then, publish manually in Studio (one tap).
- GitHub pauses scheduled runs after 60 days with no repo activity. Edit topics.csv now and then, or click Run workflow.
- Gemini's free tier has daily limits (plenty for 1 video a day). Model names change over time: if you get a "model not found" error, set a variable/secret `GEMINI_MODEL` or edit the default in generate.py.
- edge-tts is unofficial; if it breaks, update with `pip install -U edge-tts` (or ask for a replacement voice option).
- Background music (optional): put royalty-free .mp3 files from YouTube Audio Library in the `music/` folder.
- To change the voice, set `TTS_VOICE` in the workflow (list: `edge-tts --list-voices`).

## Making it earn
- YouTube Partner Program: 1,000 subscribers AND (4,000 public watch hours in 12 months OR 10 million public Shorts views in 90 days).
- Topics rotate through topics.csv. Add your own, and replace weak ones after you see what gets views.
- Check Studio analytics weekly: more of what retains viewers, fewer of what does not.
- Reply to comments, make playlists, and pin a comment with a question. Real engagement helps more than volume.
- Fill topics.csv with problems your viewers actually say (read comments on similar channels).
- Side income that pays sooner: a small Notion template for ADHD sold on Gumroad, linked in your channel About page.
