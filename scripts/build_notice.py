"""Rebuild the offline notice. Development dependency: pip install Markdown."""
from pathlib import Path
import re
import markdown

root = Path(__file__).resolve().parents[1]
source = (root / 'docs/notice-utilisation.md').read_text(encoding='utf-8')
md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'], extension_configs={'toc': {'toc_depth': '2-2'}})
body = md.convert(source)
body = re.sub(r'<table>', '<div class="table-scroll" role="region" aria-label="Tableau défilant horizontalement" tabindex="0"><table>', body).replace('</table>', '</table></div>')
css = '''
:root{color-scheme:light;--ink:#15283a;--muted:#526477;--paper:#fff;--bg:#f3f5f6;--line:#dce4e9;--teal:#096b66;--navy:#102b42}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:28px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--teal);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}a:focus-visible,button:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #de9a32;outline-offset:4px}
.skip{position:absolute;top:-100px;left:20px;background:white;padding:12px;z-index:10}.skip:focus{top:10px}
.masthead{background:var(--navy);color:white;padding:22px 4vw;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-weight:750;letter-spacing:.04em;font-size:18px}.edition{color:#bfced9;font-size:13px}.print{border:1px solid #7891a5;background:transparent;color:white;border-radius:6px;padding:10px 15px;font:inherit;font-size:13px;cursor:pointer}.print:hover{background:#284559}
.layout{max-width:1460px;margin:0 auto;display:grid;grid-template-columns:270px minmax(0,1fr);gap:38px;padding:38px 32px 70px}
aside{align-self:start;position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto;font-size:13px;padding:8px 8px 20px 0}aside summary{font-weight:750;text-transform:uppercase;letter-spacing:.13em;color:var(--muted);font-size:11px;cursor:pointer;margin-bottom:18px}.toc ul{list-style:none;margin:0;padding:0}.toc a{display:block;padding:8px 10px;text-decoration:none;border-left:2px solid transparent;color:var(--muted);line-height:1.5}.toc a:hover{color:var(--teal);border-color:var(--teal);background:#e8efef}.side-note{border-top:1px solid var(--line);margin-top:22px;padding-top:18px;color:var(--muted);font-size:12px;line-height:1.7}
main{min-width:0;background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:clamp(25px,4vw,65px);box-shadow:0 10px 35px #102b4205}.kicker{font-size:11px;font-weight:750;letter-spacing:.18em;color:var(--teal);text-transform:uppercase}h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(30px,3.4vw,48px);font-weight:500;line-height:1.15;letter-spacing:-.035em;margin:18px 0 25px;max-width:850px}h1+p{color:var(--muted);font-size:13px;margin-bottom:27px}h1+p+p{font-size:18px;color:var(--muted);line-height:1.8;border-bottom:1px solid var(--line);padding-bottom:35px}
h2{font-size:27px;line-height:1.3;letter-spacing:-.025em;margin:60px 0 24px;padding-top:20px;border-top:1px solid var(--line);color:var(--navy)}h3{font-size:19px;line-height:1.4;margin:34px 0 16px;color:var(--teal)}h4{font-size:17px}p{margin:15px 0}li{margin:8px 0}strong{font-weight:700}blockquote{margin:25px 0;padding:8px 24px;border-left:4px solid var(--teal);background:#f0f7f5;font-size:17px}blockquote p{margin:10px 0}
code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.86em;background:#edf2f5;border-radius:4px;padding:2px 5px;overflow-wrap:anywhere}pre{background:#102b42;color:#e3f2f6;border-radius:8px;padding:22px 24px;line-height:1.65;overflow-x:auto;tab-size:2;font-size:13px;margin:24px 0}pre code{padding:0;border-radius:0;background:none;color:inherit;overflow-wrap:normal;font-size:inherit;white-space:pre}
.table-scroll{width:100%;overflow-x:auto;margin:25px 0;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65;min-width:530px}th{text-align:left;color:var(--navy);background:#edf3f5;font-weight:700}th,td{padding:15px 17px;vertical-align:top;border-bottom:1px solid var(--line)}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fafcfc}
footer{margin-top:48px;padding-top:25px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:20px}.top{white-space:nowrap}
@media(max-width:1000px){.layout{grid-template-columns:220px minmax(0,1fr);gap:22px;padding:25px 20px}main{padding:30px}}
@media(max-width:760px){.masthead{padding:18px 20px}.edition{font-size:11px}.print{padding:8px 10px;font-size:12px}.layout{display:block;padding:18px 12px 40px}aside{position:static;max-height:none;background:white;border:1px solid var(--line);border-radius:8px;padding:16px;margin-bottom:18px}aside summary{margin-bottom:10px}.side-note{display:none}.toc a{padding:6px 8px}.toc ul{columns:2;column-gap:12px}.toc li{break-inside:avoid}main{padding:25px 20px}h2{font-size:24px;margin-top:45px}h1+p+p{font-size:16px}pre{padding:17px;font-size:12px}.table-scroll{margin:20px 0}footer{display:block}}
@media(max-width:420px){.toc ul{columns:1}.brand{font-size:16px}.edition{max-width:180px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@page{size:A4;margin:17mm 15mm}
@media print{html{scroll-behavior:auto}body{background:white;color:#111;font-size:10pt;line-height:1.5}.masthead{background:none;color:#15283a;border-bottom:1px solid #ccc;padding:0 0 12pt}.edition{color:#555}.print,aside,.skip,.top{display:none!important}.layout{display:block;max-width:none;margin:0;padding:0}main{border:0;border-radius:0;box-shadow:none;padding:18pt 0 0}.kicker{font-size:8pt}h1{font-size:29pt}h1+p+p{font-size:11pt;padding-bottom:12pt}h2{font-size:18pt;margin-top:24pt;padding-top:12pt}h3{font-size:13pt}h1,h2,h3,h4{break-after:avoid}p,li{orphans:3;widows:3}pre{background:#f2f4f5;color:#111;border:1px solid #ddd;font-size:8pt;white-space:pre-wrap;padding:10pt;overflow:visible;break-inside:auto}pre code{white-space:pre-wrap;overflow-wrap:anywhere}.table-scroll{overflow:visible;border-radius:0}table{min-width:0;font-size:9pt;table-layout:auto}thead{display:table-header-group}tr{break-inside:avoid}th,td{padding:7pt}code{overflow-wrap:anywhere}a{color:inherit;text-decoration:underline}footer{font-size:8pt}blockquote{break-inside:avoid}}
'''
output = '''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Notice détaillée du framework Agentic Codage : agents, orchestration, carte HTML, contrôles, coûts et utilisation pratique.">
<title>Agentic Codage — Notice d’utilisation</title><style>''' + css + '''</style></head>
<body id="haut"><a class="skip" href="#notice">Aller à la notice</a>
<header class="masthead"><div><div class="brand">AGENTIC CODAGE</div><div class="edition">Guide pratique · Version 0.2.0 · 14 septembre 2026</div></div><button class="print" type="button" onclick="window.print()">Imprimer / PDF</button></header>
<div class="layout"><aside aria-label="Sommaire"><details open><summary>Dans cette notice</summary>''' + md.toc + '''</details><p class="side-note">Lecture autonome, sans serveur ni ressource externe.<br><br>Les liens internes nécessitent de conserver la structure du dépôt. Les références externes nécessitent une connexion.</p></aside>
<main id="notice"><div class="kicker">Comprendre · organiser · vérifier</div>''' + body + '''<footer><span>Agentic Codage · Notice d’utilisation · Générée depuis la source Markdown.</span><a class="top" href="#haut">Retour en haut ↑</a></footer></main></div>
</body></html>
'''
(root / 'docs/notice-utilisation.html').write_text(output, encoding='utf-8')
print(f'HTML autonome créé : {len(output.encode())} octets ; {len(md.toc_tokens)} entrées de sommaire.')
