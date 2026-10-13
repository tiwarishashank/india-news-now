# India News Now with Nisha

Free, self-hosted podcast feed on GitHub Pages. Feed: https://tiwarishashank.github.io/india-news-now/feed.xml

## Publish an episode
Write the script as plain text (paragraphs separated by blank lines), then:

```
cd /workspace/india-news-now && AZURE_SPEECH_KEY=... python3 publish.py /path/to/script.txt --date YYYY-MM-DD
```

`--date` defaults to today (America/Los_Angeles). Re-running for the same date replaces that episode. Voice: en-IN-Aarti:DragonHDLatestNeural (Azure, westus2). The last 60 episodes are kept; older MP3s are deleted. `--no-push` builds without git push.
