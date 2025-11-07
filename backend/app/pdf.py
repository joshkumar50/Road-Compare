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
      body { font-family: Arial, sans-serif; margin: 20px; }
      .cover { background: #0F172A; color: white; padding: 40px; margin: -20px -20px 20px -20px; }
      .accent { color: #0EA5A4; }
      .issue { border: 1px solid #ddd; margin: 15px 0; padding: 12px; page-break-inside: avoid; }
      .issue h3 { margin: 0 0 8px 0; color: #1e40af; }
      .issue p { margin: 4px 0; }
      .comparison { display: flex; gap: 10px; margin-top: 10px; }
      .comparison img { max-width: 200px; max-height: 150px; border: 1px solid #ccc; }
      table { width: 100%; border-collapse: collapse; margin: 20px 0; }
      th { background: #f3f4f6; padding: 8px; text-align: left; }
      td { padding: 6px; border-bottom: 1px solid #e5e7eb; }
      .severity-HIGH { color: #dc2626; font-weight: bold; }
      .severity-MEDIUM { color: #f59e0b; font-weight: bold; }
      .severity-LOW { color: #10b981; }
    </style>
  </head>
  <body>
    <div class="cover">
      <h1>🛣️ RoadCompare Safety Inspection Report</h1>
      <h2 class="accent">Automated Road Infrastructure Analysis</h2>
      <p><strong>Job ID:</strong> {{ job.id }}</p>
      <p><strong>Status:</strong> {{ job.status | upper }}</p>
      <p><strong>Frames Analyzed:</strong> {{ job.processed_frames }}</p>
      <p><strong>Total Issues Found:</strong> {{ issues | length }}</p>
    </div>
    
    <h2>📊 Executive Summary</h2>
    <p><strong>High Severity Issues:</strong> {{ issues | selectattr('severity', 'equalto', 'HIGH') | list | length }}</p>
    <p><strong>Medium Severity Issues:</strong> {{ issues | selectattr('severity', 'equalto', 'MEDIUM') | list | length }}</p>
    <p><strong>Processing Time:</strong> {{ summary.get('processing_time', 'N/A') }}</p>
    
    <h2>🔍 Critical Issues (Top 10)</h2>
    {% for i in issues[:10] %}
    <div class="issue">
      <h3>#{{ loop.index }} - {{ i.element | replace('_', ' ') | title }}</h3>
      <p><strong>Issue:</strong> {{ i.issue_type | upper }} | <strong>Severity:</strong> <span class="severity-{{ i.severity }}">{{ i.severity }}</span></p>
      <p><strong>Confidence:</strong> {{ '%.1f'|format(i.confidence * 100) }}% | <strong>Frame:</strong> {{ i.first_frame }}</p>
      <p><strong>Reason:</strong> {{ i.reason }}</p>
      <div class="comparison">
        <div>
          <p><strong>Base (Before)</strong></p>
          <img src="{{ i.base_crop_url }}" alt="Base"/>
        </div>
        <div>
          <p><strong>Present (After)</strong></p>
          <img src="{{ i.present_crop_url }}" alt="Present"/>
        </div>
      </div>
    </div>
    {% endfor %}
    
    <h2>📋 Complete Issue List</h2>
    <table>
      <tr>
        <th>#</th>
        <th>Element</th>
        <th>Issue Type</th>
        <th>Severity</th>
        <th>Confidence</th>
        <th>Frame</th>
      </tr>
      {% for i in issues %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ i.element | replace('_', ' ') | title }}</td>
        <td>{{ i.issue_type | upper }}</td>
        <td class="severity-{{ i.severity }}">{{ i.severity }}</td>
        <td>{{ '%.1f'|format(i.confidence * 100) }}%</td>
        <td>{{ i.first_frame }}</td>
      </tr>
      {% endfor %}
    </table>
    
    <h2>🔬 Methodology</h2>
    <p>This report was generated using computer vision analysis of road infrastructure elements:</p>
    <ul>
      <li><strong>Frame Extraction:</strong> 1 frame per second from video footage</li>
      <li><strong>Element Detection:</strong> Edge detection and contour analysis with color/shape validation</li>
      <li><strong>Comparison:</strong> IoU (Intersection over Union) matching between base and present conditions</li>
      <li><strong>Elements Tracked:</strong> Sign boards, lane markings, dividers, guardrails, potholes</li>
    </ul>
    
    <h2>⚠️ Recommendations</h2>
    <ul>
      <li>Address all CRITICAL severity issues immediately</li>
      <li>Schedule repairs for MEDIUM severity issues within 30 days</li>
      <li>Monitor LOW severity issues for deterioration</li>
      <li>Conduct physical inspection to verify automated findings</li>
    </ul>
  </body>
</html>
"""
)


def generate_pdf(job: Job, issues: list[Issue]) -> bytes:
    try:
        # Limit to top 10 issues to avoid PDF size issues
        limited_issues = issues[:10]
        html = TEMPLATE.render(job=job, issues=limited_issues, summary=job.summary_json or {})
        return HTML(string=html).write_pdf()
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Fallback: generate simple PDF without images
        simple_html = f"""
        <!doctype html>
        <html>
        <head><meta charset="utf-8"/><style>body{{font-family:Arial;padding:20px;}}</style></head>
        <body>
        <h1>RoadCompare Safety Report</h1>
        <p><strong>Job ID:</strong> {job.id}</p>
        <p><strong>Status:</strong> {job.status}</p>
        <p><strong>Total Issues:</strong> {len(issues)}</p>
        <h2>Issues</h2>
        <table border="1" style="width:100%;border-collapse:collapse;">
        <tr><th>Element</th><th>Type</th><th>Severity</th><th>Frame</th></tr>
        {''.join(f'<tr><td>{i.element}</td><td>{i.issue_type}</td><td>{i.severity}</td><td>{i.first_frame}</td></tr>' for i in issues)}
        </table>
        <p><em>Note: Images omitted due to size constraints. View full report online.</em></p>
        </body>
        </html>
        """
        return HTML(string=simple_html).write_pdf()






