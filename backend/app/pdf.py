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
        # Process images - resize base64 images if too large
        processed_issues = []
        for issue in issues[:10]:  # Limit to top 10
            # Create a copy of the issue data
            issue_dict = {
                'id': issue.id,
                'element': issue.element,
                'issue_type': issue.issue_type,
                'severity': issue.severity,
                'confidence': issue.confidence,
                'first_frame': issue.first_frame,
                'reason': issue.reason,
                'base_crop_url': issue.base_crop_url[:500] + '...' if len(issue.base_crop_url) > 500 else issue.base_crop_url,
                'present_crop_url': issue.present_crop_url[:500] + '...' if len(issue.present_crop_url) > 500 else issue.present_crop_url
            }
            processed_issues.append(issue_dict)
        
        # Generate PDF without images first
        simple_template = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #0F172A; color: white; padding: 30px; margin: -20px -20px 20px -20px; }
        h1 { margin: 0; }
        .subtitle { color: #0EA5A4; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #f3f4f6; padding: 10px; text-align: left; border: 1px solid #ddd; }
        td { padding: 8px; border: 1px solid #ddd; }
        .HIGH { color: #dc2626; font-weight: bold; }
        .MEDIUM { color: #f59e0b; font-weight: bold; }
        .issue-box { border: 1px solid #ddd; padding: 15px; margin: 15px 0; background: #f9fafb; }
        .meta { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛣️ RoadCompare Safety Inspection Report</h1>
        <div class="subtitle">Automated Road Infrastructure Analysis</div>
    </div>
    
    <h2>📊 Job Information</h2>
    <table>
        <tr><th>Job ID</th><td>{{ job.id }}</td></tr>
        <tr><th>Status</th><td>{{ job.status | upper }}</td></tr>
        <tr><th>Frames Analyzed</th><td>{{ job.processed_frames }}</td></tr>
        <tr><th>Total Issues</th><td>{{ issues | length }}</td></tr>
        <tr><th>High Severity</th><td>{{ issues | selectattr('severity', 'equalto', 'HIGH') | list | length }}</td></tr>
        <tr><th>Medium Severity</th><td>{{ issues | selectattr('severity', 'equalto', 'MEDIUM') | list | length }}</td></tr>
    </table>
    
    <h2>🔍 Detected Issues</h2>
    {% for issue in issues %}
    <div class="issue-box">
        <h3>#{{ loop.index }} - {{ issue.element | replace('_', ' ') | title }}</h3>
        <p class="meta">
            <strong>Type:</strong> {{ issue.issue_type | upper }} | 
            <strong>Severity:</strong> <span class="{{ issue.severity }}">{{ issue.severity }}</span> | 
            <strong>Confidence:</strong> {{ '%.1f'|format(issue.confidence * 100) }}% | 
            <strong>Frame:</strong> {{ issue.first_frame }}
        </p>
        <p><strong>Analysis:</strong> {{ issue.reason }}</p>
    </div>
    {% endfor %}
    
    <h2>📋 Summary Table</h2>
    <table>
        <tr>
            <th>#</th>
            <th>Element</th>
            <th>Issue Type</th>
            <th>Severity</th>
            <th>Confidence</th>
            <th>Frame</th>
        </tr>
        {% for issue in issues %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ issue.element | replace('_', ' ') | title }}</td>
            <td>{{ issue.issue_type | upper }}</td>
            <td class="{{ issue.severity }}">{{ issue.severity }}</td>
            <td>{{ '%.1f'|format(issue.confidence * 100) }}%</td>
            <td>{{ issue.first_frame }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>✅ Recommendations</h2>
    <ul>
        <li><strong>CRITICAL:</strong> Address immediately - safety hazard</li>
        <li><strong>MEDIUM:</strong> Schedule repairs within 30 days</li>
        <li>Physical inspection recommended to verify findings</li>
        <li>View online report for visual comparisons</li>
    </ul>
    
    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em;">
        Generated: {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}<br>
        Note: For visual comparisons, please view the online report.
    </p>
</body>
</html>
"""
        from jinja2 import Template
        from datetime import datetime
        template = Template(simple_template)
        html = template.render(job=job, issues=issues, datetime=datetime)
        return HTML(string=html).write_pdf()
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        # Ultra simple fallback
        fallback = f"""<!doctype html><html><body>
        <h1>RoadCompare Report</h1>
        <p>Job: {job.id}</p>
        <p>Issues Found: {len(issues)}</p>
        <ul>{''.join(f'<li>{i.element} - {i.issue_type} ({i.severity})</li>' for i in issues[:10])}</ul>
        </body></html>"""
        return HTML(string=fallback).write_pdf()






