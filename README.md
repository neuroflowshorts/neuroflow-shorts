# NeuroFlow Shorts Bot (100% free)

Makes and uploads one YouTube Short per day for the NeuroFlow channel
(gentle productivity for ADHD / autistic / anxious brains).
Runs in the cloud on GitHub Actions, so your computer can stay off after setup.

Pipeline: topic (topics.csv) -> Gemini writes script -> edge-tts voice -> Pixabay stock clips
-> ffmpeg adds hook title + captions + loudness fix -> YouTube upload.

## Files
- generate.py        makes the video (script, voice, clips, captions, hook title)
- upload.py          uploads output/short.mp4 to YouTube
- get_token.py       run ONCE on your own computer to get the YouTube login token
- topics.csv         list of topics (one per line), rotates daily. Add your own!
- requirements.txt   Python packages
- .github/workflows/daily.yml   the daily schedule
- music/             optional royalty-free .mp3 files for quiet background music

## One-time setup

### 1. Free API keys (never share them in chat or code)
- Gemini: https://aistudio.google.com/apikey -> Create API key
- Pixabay (stock videos): sign up at https://pixabay.com, then open https://pixabay.com/api/docs/ while logged in. Your key is shown there.
  (Without a Pixabay key the bot still works with a plain dark background.)

### 2. YouTube upload access (Google Cloud, no billing needed)
1. https://console.cloud.google.com -> create project `neuroflow-bot`.
2. Enable "YouTube Data API v3".
3. Google Auth Platform (OAuth consent screen): External, app name + your email.
4. Audience -> PUBLISH APP so the status is "In production".
   If it stays in "Testing", the login expires after 7 days and the bot stops.
   (You will see an "unverified app" warning when logging in. For your own channel: Advanced -> Continue.)
5. Clients -> Create client -> Desktop app -> Download JSON. Rename to `client_secret.json`,
   put it next to get_token.py.
6. On your computer (Python installed):  pip install google-auth-oauthlib   then   python get_token.py
   Log in with the Google account that owns NeuroFlow. It prints 3 values: copy them.

### 3. GitHub
1. Repo: github.com/<you>/neuroflow-shorts (public = unlimited free Actions minutes).
2. Upload all files, including `.github/workflows/daily.yml`.
3. Settings -> Secrets and variables -> Actions -> Secrets. Add:
   GEMINI_API_KEY, PIXABAY_API_KEY, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
   Direct link: https://github.com/<you>/neuroflow-shorts/settings/secrets/actions
4. Same page, "Variables" tab (all optional):
   - PRIVACY  = private (default) or public
   - AI_LABEL = true (default) or false  -> ticks YouTube's "altered/synthetic content" box
   - TTS_VOICE = a different edge-tts voice (e.g. en-IN-NeerjaNeural)

### 4. Test
Actions tab -> "Daily NeuroFlow Short" -> Run workflow. After ~3 to 6 minutes:
- download the `short` artifact to preview the video
- check YouTube Studio for the upload

## Daily routine (2 minutes)
- Start with PRIVACY=private. Open YouTube Studio on your phone, watch the Short, press Publish if good.
- After ~2 weeks of good results, set PRIVACY=public for hands-off posting. Still skim the channel weekly.

## About the AI label
- The narration is AI (text-to-speech) and the visuals are real stock footage.
- Descriptions say so, and the AI label is ticked by default (AI_LABEL=true).
- YouTube's rules change. Read the question in YouTube Studio the first time you upload. If you ever add
  realistic AI people, places or events, the label is required.

## Troubleshooting
- Gemini "404 model no longer available": models change. generate.py already tries several names.
  You can also set a variable/secret GEMINI_MODEL to a newer model name.
- Gemini "503 high demand": temporary. The bot retries and switches model. If it still fails, Run workflow again later.
- "Upload to YouTube" red: check the 3 YT_ secrets, and that the OAuth app is "In production".
- Uploads stay private: Google may force private until your API project passes an audit. Publish manually in Studio.
- GitHub pauses scheduled runs after 60 days with no repo activity. Click Run workflow now and then.
- Never put keys in files, screenshots, or chat. If one leaks, delete it and create a new one.

## Making it earn
- YouTube Partner Program: 1,000 subscribers AND (4,000 public watch hours in 12 months OR 10 million public Shorts views in 90 days).
- Review Studio analytics weekly: keep topics that hold viewers, replace the rest in topics.csv.
- Reply to comments, make playlists, pin a comment with a question. Real engagement beats volume.
- Side income that pays sooner: freelance work, or a small ADHD Notion template on Gumroad linked in your About page.
