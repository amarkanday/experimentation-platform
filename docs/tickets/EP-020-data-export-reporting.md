# EP-020: Data Export & Reporting Features

**Status:** 🔴 Not Started
**Priority:** 🟡 Medium (Priority 2 feature)
**Story Points:** 5
**Sprint:** Phase 4 - Frontend Development (Week 9)
**Assignee:** Frontend + Backend Team
**Created:** 2025-12-16
**Type:** Feature

---

## 📋 Overview

### User Story
**As a** product manager, analyst, or stakeholder
**I want** to export experiment results and generate reports
**So that** I can analyze data offline, share with stakeholders, and create presentations

### Business Value
- **Flexibility:** Offline analysis with preferred tools
- **Sharing:** Easy stakeholder communication
- **Compliance:** Audit trail and record keeping
- **Insights:** Deep-dive analysis in Excel/Python

---

## 🎯 Problem Statement

### Current State
- ✅ Results visible in web dashboard
- ✅ Backend provides JSON API responses
- ❌ **Missing:** CSV export functionality
- ❌ **Missing:** Excel export with formatting
- ❌ **Missing:** PDF report generation
- ❌ **Missing:** Scheduled exports
- ❌ **Missing:** User activity reporting
- ❌ **Missing:** Audit trail reporting

### User Pain Points
1. Can't export data for offline analysis
2. Have to manually screenshot for presentations
3. Can't generate reports for stakeholders
4. No historical trend reporting
5. Can't schedule automated reports
6. No audit trail exports for compliance

---

## 🔧 Technical Specifications

### Export Formats

```typescript
enum ExportFormat {
  CSV = 'csv',           // Raw data, good for Excel
  JSON = 'json',         // Raw data, good for programming
  EXCEL = 'xlsx',        // Formatted with charts
  PDF = 'pdf',           // Presentation-ready report
}

enum ExportType {
  EXPERIMENT_RESULTS = 'experiment_results',
  RAW_EVENTS = 'raw_events',
  USER_ACTIVITY = 'user_activity',
  AUDIT_LOG = 'audit_log',
  METRICS_SUMMARY = 'metrics_summary',
}
```

### API Endpoints

```typescript
// Export endpoints
POST /api/v1/exports/create
GET  /api/v1/exports/{export_id}
GET  /api/v1/exports/{export_id}/download
GET  /api/v1/exports/list

// Report endpoints
POST /api/v1/reports/generate
GET  /api/v1/reports/{report_id}
POST /api/v1/reports/schedule
GET  /api/v1/reports/scheduled
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│              User Request                        │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────▼────────┐
        │  API Handler  │
        └──────┬────────┘
               │
        ┌──────▼────────┐
        │ Export Service│
        └──────┬────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼────────┐ ┌────▼───────────┐
│  Data Query   │ │  Formatter     │
│  Service      │ │  (CSV/PDF/XLS) │
└──────┬────────┘ └────┬───────────┘
       │               │
       │        ┌──────▼────────┐
       │        │  S3 Storage   │
       │        └──────┬────────┘
       │               │
       └───────────────┴───────────┐
                                   │
                          ┌────────▼────────┐
                          │  Download URL   │
                          │  (Pre-signed)   │
                          └─────────────────┘
```

---

## 📝 Implementation Tasks

### Phase 1: Backend Export Service (1 day)

- [ ] **Task 1.1:** Create export service
  ```python
  # backend/app/services/export_service.py
  class ExportService:
      async def create_export(
          self,
          export_type: ExportType,
          format: ExportFormat,
          filters: dict,
          user_id: str
      ) -> Export:
          """Create async export job"""
          pass

      async def generate_export(self, export_id: str):
          """Generate export file"""
          pass

      async def get_download_url(self, export_id: str) -> str:
          """Get presigned S3 URL"""
          pass
  ```

- [ ] **Task 1.2:** Implement CSV export
  ```python
  import csv
  import io

  def export_to_csv(data: list[dict]) -> bytes:
      output = io.StringIO()
      writer = csv.DictWriter(output, fieldnames=data[0].keys())
      writer.writeheader()
      writer.writerows(data)
      return output.getvalue().encode('utf-8')
  ```

- [ ] **Task 1.3:** Implement Excel export
  ```python
  from openpyxl import Workbook
  from openpyxl.chart import BarChart

  def export_to_excel(data: dict) -> bytes:
      wb = Workbook()
      ws = wb.active
      # Add data
      # Add formatting
      # Add charts
      return wb.save_to_bytes()
  ```

- [ ] **Task 1.4:** Implement JSON export
  ```python
  import json

  def export_to_json(data: any) -> bytes:
      return json.dumps(data, indent=2).encode('utf-8')
  ```

- [ ] **Task 1.5:** Set up S3 storage for exports
  ```python
  # Store exports in S3
  s3_key = f"exports/{user_id}/{export_id}.{format}"
  s3_client.put_object(
      Bucket='exports-bucket',
      Key=s3_key,
      Body=export_data,
      ServerSideEncryption='AES256'
  )

  # Generate presigned URL (expires in 1 hour)
  download_url = s3_client.generate_presigned_url(
      'get_object',
      Params={'Bucket': 'exports-bucket', 'Key': s3_key},
      ExpiresIn=3600
  )
  ```

### Phase 2: PDF Report Generation (1 day)

- [ ] **Task 2.1:** Set up ReportLab for PDF generation
  ```python
  from reportlab.lib.pagesizes import letter
  from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
  from reportlab.lib.styles import getSampleStyleSheet

  def generate_pdf_report(experiment: dict) -> bytes:
      buffer = io.BytesIO()
      doc = SimpleDocTemplate(buffer, pagesize=letter)
      # Add content
      doc.build(story)
      return buffer.getvalue()
  ```

- [ ] **Task 2.2:** Create report templates
  - Executive summary template
  - Detailed results template
  - Comparison report template

- [ ] **Task 2.3:** Add charts to PDF
  ```python
  from reportlab.graphics.shapes import Drawing
  from reportlab.graphics.charts.barcharts import VerticalBarChart

  def create_chart_image(data: dict) -> Drawing:
      # Create chart
      # Return as Drawing object
      pass
  ```

- [ ] **Task 2.4:** Implement branded templates
  - Company logo
  - Custom colors
  - Consistent formatting
  - Page headers/footers

### Phase 3: Frontend Export UI (0.5 days)

- [ ] **Task 3.1:** Add export button to results page
  ```tsx
  <ExportButton
    onExport={(format) => handleExport(format)}
    formats={['csv', 'excel', 'pdf', 'json']}
  />
  ```

- [ ] **Task 3.2:** Create export modal
  ```tsx
  <ExportModal
    isOpen={showExport}
    onClose={() => setShowExport(false)}
    onSubmit={handleExportRequest}
  >
    <FormatSelector />
    <DateRangeSelector />
    <FieldSelector />
    <ExportButton />
  </ExportModal>
  ```

- [ ] **Task 3.3:** Show export progress
  ```tsx
  <ExportProgress
    status={exportStatus}
    progress={exportProgress}
    onCancel={cancelExport}
  />
  ```

- [ ] **Task 3.4:** Auto-download when ready
  ```typescript
  useEffect(() => {
    if (exportStatus === 'completed') {
      window.location.href = downloadUrl;
    }
  }, [exportStatus]);
  ```

### Phase 4: Scheduled Reports (1 day)

- [ ] **Task 4.1:** Create scheduled report model
  ```python
  class ScheduledReport(Base):
      id = Column(UUID, primary_key=True)
      user_id = Column(UUID, ForeignKey('users.id'))
      name = Column(String)
      report_type = Column(Enum(ReportType))
      schedule = Column(String)  # Cron expression
      format = Column(Enum(ExportFormat))
      recipients = Column(ARRAY(String))
      filters = Column(JSONB)
      is_active = Column(Boolean, default=True)
  ```

- [ ] **Task 4.2:** Implement scheduler
  ```python
  from apscheduler.schedulers.asyncio import AsyncIOScheduler

  scheduler = AsyncIOScheduler()

  @scheduler.scheduled_job('cron', hour=8)  # Daily at 8am
  async def generate_daily_reports():
      reports = await get_scheduled_reports()
      for report in reports:
          await generate_and_email_report(report)
  ```

- [ ] **Task 4.3:** Email delivery
  ```python
  import boto3

  def send_report_email(recipients: list, report_url: str):
      ses = boto3.client('ses')
      ses.send_email(
          Source='reports@example.com',
          Destination={'ToAddresses': recipients},
          Message={
              'Subject': {'Data': 'Your Scheduled Report'},
              'Body': {
                  'Html': {'Data': f'<a href="{report_url}">Download Report</a>'}
              }
          }
      )
  ```

- [ ] **Task 4.4:** Create schedule management UI
  ```tsx
  <ScheduledReports>
    <ReportList />
    <CreateReportButton />
    <ScheduleEditor />
  </ScheduledReports>
  ```

### Phase 5: User Activity Reporting (0.5 days)

- [ ] **Task 5.1:** Create user activity report query
  ```sql
  SELECT
    u.username,
    u.email,
    COUNT(DISTINCT e.id) as experiments_created,
    COUNT(DISTINCT ff.id) as flags_created,
    COUNT(DISTINCT al.id) as total_actions,
    MAX(al.created_at) as last_activity
  FROM users u
  LEFT JOIN experiments e ON e.created_by = u.id
  LEFT JOIN feature_flags ff ON ff.created_by = u.id
  LEFT JOIN audit_logs al ON al.user_id = u.id
  WHERE al.created_at >= :start_date
  GROUP BY u.id
  ```

- [ ] **Task 5.2:** Add activity report endpoint
  ```python
  @router.get("/reports/user-activity")
  async def get_user_activity_report(
      start_date: datetime,
      end_date: datetime,
      format: ExportFormat = ExportFormat.CSV
  ):
      data = await report_service.get_user_activity(start_date, end_date)
      return export_service.export(data, format)
  ```

- [ ] **Task 5.3:** Create activity dashboard
  - Most active users
  - Team activity trends
  - Feature usage stats

### Phase 6: Audit Log Export (0.5 days)

- [ ] **Task 6.1:** Add audit log export
  ```python
  @router.get("/reports/audit-logs")
  async def export_audit_logs(
      start_date: datetime,
      end_date: datetime,
      entity_type: Optional[str] = None,
      action: Optional[str] = None,
      format: ExportFormat = ExportFormat.CSV
  ):
      logs = await audit_service.get_logs(
          start_date=start_date,
          end_date=end_date,
          entity_type=entity_type,
          action=action
      )
      return export_service.export(logs, format)
  ```

- [ ] **Task 6.2:** Add compliance report
  - All admin actions
  - Data access logs
  - Permission changes
  - Configuration changes

### Phase 7: Testing & Documentation (0.5 days)

- [ ] **Task 7.1:** Unit tests for export service
- [ ] **Task 7.2:** Integration tests for export flow
- [ ] **Task 7.3:** Test large exports (10K+ rows)
- [ ] **Task 7.4:** Document export API
- [ ] **Task 7.5:** Create user guide for exports

---

## ✅ Acceptance Criteria

### Export Functionality
- [ ] Export to CSV works for all data types
- [ ] Export to Excel includes formatting and charts
- [ ] Export to PDF generates presentation-ready reports
- [ ] Export to JSON preserves data structure
- [ ] Exports handle 10K+ rows without timeout

### User Experience
- [ ] Export button visible on all relevant pages
- [ ] Progress indicator during export generation
- [ ] Auto-download when ready
- [ ] Clear error messages on failure
- [ ] Can cancel long-running exports

### Scheduled Reports
- [ ] Can schedule daily/weekly/monthly reports
- [ ] Reports sent via email automatically
- [ ] Can manage (edit/delete) scheduled reports
- [ ] Email contains download link (24h expiry)
- [ ] Failed reports trigger alert

### Performance
- [ ] Exports complete in < 30 seconds for 1K rows
- [ ] Exports complete in < 5 minutes for 100K rows
- [ ] Large exports don't block other requests
- [ ] S3 storage has lifecycle policy (delete after 7 days)
- [ ] Presigned URLs expire after 1 hour

### Security
- [ ] Users can only export their own data
- [ ] Admins can export all data
- [ ] Audit log for all exports
- [ ] Sensitive data redacted in exports
- [ ] S3 objects encrypted at rest

---

## ✔️ Definition of Done

### Implementation
- [ ] All export formats working
- [ ] Scheduled reports functional
- [ ] User activity reporting available
- [ ] Audit log export working

### Testing
- [ ] Unit tests > 85% coverage
- [ ] Integration tests passing
- [ ] Load tested with 100K rows
- [ ] Cross-browser testing complete

### Documentation
- [ ] API documentation updated
- [ ] User guide created
- [ ] Report templates documented
- [ ] Schedule syntax explained

### Performance
- [ ] Export benchmarks met
- [ ] No memory leaks
- [ ] S3 costs estimated
- [ ] Monitoring dashboards updated

---

## 📊 Dependencies

### Blocked By
- None (independent feature)

### Blocking
- None (nice-to-have feature)

### Related Tickets
- EP-015: Enhanced Results Visualization (exports from dashboards)
- EP-014: Documentation (user guides)

---

## 🚨 Risks & Mitigation

### Risk 1: Large Export Timeouts
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- Async export generation
- Background job processing
- Email notification when ready
- Pagination for very large exports

### Risk 2: S3 Storage Costs
**Impact:** Low
**Probability:** High
**Mitigation:**
- 7-day lifecycle policy
- Compression before storage
- Monitor storage usage
- Alert on unexpected costs

### Risk 3: Email Delivery Failures
**Impact:** Low
**Probability:** Low
**Mitigation:**
- Retry logic for failures
- In-app notification fallback
- SES bounce handling
- Monitor delivery rates

---

## 📈 Success Metrics

### Usage
- 50% of users export data monthly
- 100+ exports per month
- 20% adoption of scheduled reports

### Performance
- 95% of exports complete in < 30 seconds
- 99.9% export success rate
- < 1% storage cost of total infrastructure

### User Satisfaction
- 90% find exports useful
- < 5 support tickets about exports
- Positive feedback on report quality

---

## 📚 Reference Materials

### Libraries
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel generation
- [ReportLab](https://www.reportlab.com/) - PDF generation
- [APScheduler](https://apscheduler.readthedocs.io/) - Job scheduling

### AWS Services
- [S3 Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- [SES Email Sending](https://docs.aws.amazon.com/ses/)

---

## 🔄 Change Log

| Date       | Author | Change Description |
|------------|--------|-------------------|
| 2025-12-16 | Claude | Initial ticket creation |

---

**Estimated Completion:** 5 working days (1 week)
**Target Sprint:** Q1 2026, Sprint 9
**Priority:** Medium (Priority 2 feature from development plan)
