#!/usr/bin/env python3
"""Publish an Indian News Today episode. Usage: python3 publish.py SCRIPT.txt [--date YYYY-MM-DD] [--no-push]"""
import os,sys,re,json,time,html,shutil,subprocess,argparse,datetime,tempfile,urllib.request,urllib.error
from email.utils import format_datetime
from zoneinfo import ZoneInfo
REPO=os.path.dirname(os.path.abspath(__file__))
BASE="https://tiwarishashank.github.io/india-news-now/"
ENDPOINT="https://westus2.tts.speech.microsoft.com/cognitiveservices/v1"
VOICE="en-IN-Aarti:DragonHDLatestNeural"
KEEP=60
TITLE="Indian News Today with Nisha"
DESC=("A daily two-to-three minute bulletin of India's top news: politics, business and markets, entertainment and cricket. "
      "Nisha is an AI-voiced newsreader; stories are researched and checked by an AI assistant.")
def sh(*a,**k): return subprocess.run(a,check=True,cwd=REPO,**k)
def ensure_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        subprocess.run("sudo apt-get update && sudo apt-get install -y ffmpeg",shell=True,check=True)
def chunks(paras,limit=5000):
    out,cur=[],[]
    for p in paras:
        if cur and sum(len(x) for x in cur)+len(p)>limit: out.append(cur); cur=[]
        cur.append(p)
    if cur: out.append(cur)
    return out
def ssml(paras):
    body='<break time="700ms"/>'.join(html.escape(p,quote=False) for p in paras)
    return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-IN">'
            f'<voice name="{VOICE}">{body}</voice></speak>')
def tts(text_ssml,out):
    key=os.environ["AZURE_SPEECH_KEY"]
    for i in range(6):
        req=urllib.request.Request(ENDPOINT,data=text_ssml.encode(),method="POST",headers={
            "Ocp-Apim-Subscription-Key":key,"Content-Type":"application/ssml+xml",
            "X-Microsoft-OutputFormat":"audio-24khz-96kbitrate-mono-mp3","User-Agent":"india-news-now"})
        try:
            with urllib.request.urlopen(req,timeout=120) as r: open(out,"wb").write(r.read()); return
        except urllib.error.HTTPError as e:
            if e.code==429 or e.code>=500:
                time.sleep(int(e.headers.get("Retry-After") or 2**i*3)); continue
            raise SystemExit(f"TTS failed HTTP {e.code}: {e.read()[:300]!r}")
        except urllib.error.URLError: time.sleep(2**i*3)
    raise SystemExit("TTS failed after retries")
def duration(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).strip())
def hms(s): s=int(round(s)); return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"
def x(s): return html.escape(s,quote=True)
def build_feed(eps):
    now=format_datetime(datetime.datetime.now(datetime.timezone.utc))
    items=[]
    for e in eps:
        items.append(f"""  <item>
    <title>{x(e['title'])}</title>
    <description>{x(e['description'])}</description>
    <itunes:summary>{x(e['description'])}</itunes:summary>
    <guid isPermaLink="false">india-news-now-{e['date']}</guid>
    <pubDate>{e['pubDate']}</pubDate>
    <enclosure url="{BASE}episodes/{e['date']}.mp3" length="{e['length']}" type="audio/mpeg"/>
    <itunes:duration>{e['duration']}</itunes:duration>
    <itunes:episodeType>full</itunes:episodeType>
    <itunes:explicit>false</itunes:explicit>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>{x(TITLE)}</title>
  <link>{BASE}</link>
  <atom:link href="{BASE}feed.xml" rel="self" type="application/rss+xml"/>
  <description>{x(DESC)}</description>
  <itunes:summary>{x(DESC)}</itunes:summary>
  <language>en-in</language>
  <copyright>© {datetime.date.today().year} Shashank Tiwari</copyright>
  <lastBuildDate>{now}</lastBuildDate>
  <itunes:author>Shashank Tiwari</itunes:author>
  <itunes:owner><itunes:name>Shashank Tiwari</itunes:name><itunes:email>shashank.iitb@gmail.com</itunes:email></itunes:owner>
  <itunes:image href="{BASE}cover.jpg"/>
  <image><url>{BASE}cover.jpg</url><title>{x(TITLE)}</title><link>{BASE}</link></image>
  <itunes:category text="News"><itunes:category text="Daily News"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
{chr(10).join(items)}
</channel>
</rss>
"""
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("--date"); ap.add_argument("--no-push",action="store_true")
    a=ap.parse_args()
    ensure_ffmpeg()
    date=a.date or datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    d=datetime.date.fromisoformat(date)
    text=open(a.script,encoding="utf-8").read()
    paras=[re.sub(r"\s+"," ",p).strip() for p in re.split(r"\n\s*\n",text) if p.strip()]
    if len(paras)<=1: paras=[l.strip() for l in text.splitlines() if l.strip()]
    os.makedirs(f"{REPO}/episodes",exist_ok=True); os.makedirs(f"{REPO}/scripts",exist_ok=True)
    mp3=f"{REPO}/episodes/{date}.mp3"
    with tempfile.TemporaryDirectory() as td:
        parts=[]
        for i,c in enumerate(chunks(paras)):
            p=f"{td}/p{i}.mp3"; tts(ssml(c),p); parts.append(p)
        if len(parts)==1: shutil.copy(parts[0],mp3)
        else:
            open(f"{td}/l.txt","w").write("".join(f"file '{p}'\n" for p in parts))
            subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{td}/l.txt","-c","copy",mp3],check=True)
    sp=f"{REPO}/scripts/{date}.txt"
    if os.path.abspath(a.script)!=os.path.abspath(sp): shutil.copy(a.script,sp)
    mf=f"{REPO}/episodes.json"
    eps=json.load(open(mf)) if os.path.exists(mf) else []
    eps=[e for e in eps if e["date"]!=date]
    pub=datetime.datetime.combine(d,datetime.time(6,47),ZoneInfo("America/Los_Angeles"))
    summary=paras[1] if len(paras)>1 else paras[0]
    eps.append({"date":date,"title":f"Indian News Today – {d.strftime('%A, %B')} {d.day}, {d.year}",
        "description":(summary[:400]+("…" if len(summary)>400 else "")),
        "pubDate":format_datetime(pub),"length":os.path.getsize(mp3),"duration":hms(duration(mp3))})
    eps.sort(key=lambda e:e["date"],reverse=True)
    keep,old=eps[:KEEP],eps[KEEP:]
    for e in old:
        for f in (f"{REPO}/episodes/{e['date']}.mp3",f"{REPO}/scripts/{e['date']}.txt"):
            if os.path.exists(f): os.remove(f)
    keepd={e["date"] for e in keep}
    for f in os.listdir(f"{REPO}/episodes"):
        if f.endswith(".mp3") and f[:-4] not in keepd: os.remove(f"{REPO}/episodes/{f}")
    json.dump(keep,open(mf,"w"),indent=1,ensure_ascii=False)
    open(f"{REPO}/feed.xml","w",encoding="utf-8").write(build_feed(keep))
    import xml.dom.minidom; xml.dom.minidom.parse(f"{REPO}/feed.xml")
    if not os.path.exists(f"{REPO}/.nojekyll"): open(f"{REPO}/.nojekyll","w").close()
    if a.no_push: print("built",mp3); return
    sh("git","add","-A")
    if subprocess.run(["git","diff","--cached","--quiet"],cwd=REPO).returncode:
        sh("git","commit","-q","-m",f"Episode {date}")
    if subprocess.run(["git","ls-remote","--exit-code","--heads","origin","main"],cwd=REPO,capture_output=True).returncode==0:
        sh("git","pull","-q","--rebase","origin","main")
    sh("git","push","-q","origin","HEAD:main")
    print("published",BASE+f"episodes/{date}.mp3")
if __name__=="__main__": main()
