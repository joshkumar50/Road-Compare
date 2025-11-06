from weasyprint import HTML
from jinja2 import Template
from .models import Job, Issue


TEMPLATE = Template(
    """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <style>
      body { font-family: Arial, sans-serif; }
      .cover { background: #0F172A; color: white; padding: 40px; }
      .accent { color: #0EA5A4; }
      .issue { border: 1px solid #ddd; margin: 10px 0; padding: 8px; }
      .thumb { height: 100px; }
    </style>
  </head>
  <body>
    <div class="cover">
      <h1>RoadCompare</h1>
      <h2 class="accent">Automated Comparative Road Safety Audit — RoadCompare</h2>
      <p>Job ID: {{ job.id }} | Status: {{ job.status }} | Processed frames: {{ job.processed_frames }}</p>
    </div>
    <h2>Summary</h2>
    <pre>{{ summary | tojson }}</pre>
    <h2>Top Issues</h2>
    {% for i in issues[:5] %}
    <div class="issue">
      <h3>#{{ loop.index }} {{ i.element }} — {{ i.issue_type }} ({{ i.severity }})</h3>
      <p>Confidence: {{ '%.2f'|format(i.confidence) }}</p>
      <p>{{ i.reason }}</p>
      <img class="thumb" src="{{ i.base_crop_url }}"/> → <img class="thumb" src="{{ i.present_crop_url }}"/>
    </div>
    {% endfor %}
    <h2>All Issues</h2>
    <table style="width:100%; border-collapse: collapse;" border="1">
      <tr><th>ID</th><th>Element</th><th>Type</th><th>Severity</th><th>Conf.</th><th>Frames</th></tr>
      {% for i in issues %}
      <tr>
        <td>{{ i.id }}</td><td>{{ i.element }}</td><td>{{ i.issue_type }}</td><td>{{ i.severity }}</td>
        <td>{{ '%.2f'|format(i.confidence) }}</td><td>{{ i.first_frame }}–{{ i.last_frame }}</td>
      </tr>
      {% endfor %}
    </table>
    <h2>Methodology</h2>
    <p>YOLOv8 detections on extracted frames (1 FPS). Alignment using ORB+RANSAC. Change types via IoU match and mask SSIM for lane/pavement. Persistence N=3.</p>
    <h2>Limitations</h2>
    <ul><li>Lighting/weather variations</li><li>Camera pose differences</li><li>Small sample for demo</li></ul>
  </body>
 </html>
"""
)


def generate_pdf(job: Job, issues: list[Issue]) -> bytes:
    html = TEMPLATE.render(job=job, issues=issues, summary=job.summary_json)
    return HTML(string=html).write_pdf()






