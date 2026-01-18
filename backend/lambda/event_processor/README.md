# Event Processor Lambda

AWS Lambda function for processing event streams from Kinesis with real-time metric aggregation and S3 archival.

## Overview

The Event Processor Lambda is a serverless function that processes events from Kinesis streams, validates them, enriches with experiment/assignment data, aggregates metrics to DynamoDB, and archives to S3 for long-term storage.

## Architecture

### Processing Pipeline

```
Kinesis → Parse → Validate → Enrich → Aggregate → Archive → Response
```

1. **Parse**: Decode base64-encoded Kinesis events and parse JSON
2. **Validate**: Validate events using Pydantic schemas
3. **Enrich**: Add assignment and experiment metadata from DynamoDB
4. **Aggregate**: Update real-time metric counters in DynamoDB
5. **Archive**: Compress and store events in S3 with date partitioning
6. **Response**: Return partial batch failures for Kinesis retry

### Modules

- `handler.py` - Lambda entry point, initializes AWS clients
- `event_parser.py` - Kinesis event parsing and base64 decoding
- `event_validator.py` - Pydantic-based event validation
- `event_enricher.py` - Event enrichment with assignment/experiment data
- `event_aggregator.py` - Real-time DynamoDB metric aggregation
- `s3_archiver.py` - S3 archival with gzip compression
- `batch_processor.py` - Pipeline orchestration and error handling

## Features

### Event Parsing
- Base64 decoding of Kinesis data
- JSON parsing with error recovery
- Batch processing with partial failure support
- UTF-8 character support

### Event Validation
- Pydantic V2 schema validation
- Required field enforcement
- Type checking
- Duplicate detection
- Nested structure preservation

### Event Enrichment
- Assignment data fetching from DynamoDB
- Experiment metadata addition
- Derived field calculation (e.g., time since assignment)
- Graceful handling of missing data

### Metric Aggregation
- Atomic DynamoDB counter increments
- Time-windowed aggregation (hourly/daily)
- Unique user tracking per variant
- Concurrent update handling with retries
- Race condition prevention

### S3 Archival
- Date-based partitioning: `year=YYYY/month=MM/day=DD/hour=HH/`
- gzip compression for storage efficiency
- Batching by size (5MB) and count (1000 events)
- Retry logic for transient failures
- Metadata tagging

### Error Handling
- Partial batch failure reporting
- Dead Letter Queue (DLQ) integration
- Comprehensive error metrics
- CloudWatch logging
- Graceful degradation

## Configuration

### Environment Variables

- `S3_BUCKET` - S3 bucket for event archival (default: `event-archive`)
- `DYNAMODB_TABLE` - DynamoDB table for aggregations (default: `event-aggregations`)
- `DLQ_URL` - SQS queue URL for dead letter queue (optional)

### AWS Resources Required

- **Kinesis Stream**: Source of events
- **DynamoDB Table**: For metric aggregations
  - Partition Key: `partition_key` (String)
  - Sort Key: `sort_key` (String)
- **S3 Bucket**: For event archival
- **SQS Queue**: Optional DLQ for failed events
- **IAM Role**: With permissions for Kinesis, DynamoDB, S3, SQS, CloudWatch Logs

## Performance

### Benchmarks (from tests)

- **Throughput**: 100 events processed in < 1000ms
- **Error Rate**: < 0.1% for valid events
- **Latency**: Sub-second processing for typical batches

### Optimization Features

- AWS client initialization on cold start
- Efficient batch processing
- Connection pooling
- Minimal memory footprint

## Testing

### Test Coverage: 70 tests, 100% passing

```bash
# Run all tests
pytest backend/lambda/event_processor/tests/ -v

# Run specific test module
pytest backend/lambda/event_processor/tests/test_handler.py -v
```

### Test Categories

1. **Unit Tests** (58 tests):
   - Kinesis parsing (8 tests)
   - Event validation (12 tests)
   - Event enrichment (8 tests)
   - Metric aggregation (10 tests)
   - S3 archival (10 tests)
   - Batch processing (10 tests)

2. **Integration Tests** (12 tests):
   - End-to-end Lambda handler
   - Performance benchmarks
   - Error rate validation
   - CloudWatch logging

## Development

### TDD Approach

This Lambda was built using Test-Driven Development (TDD):

🔴 **RED**: Write failing tests first
🟢 **GREEN**: Implement minimal code to pass tests
🔵 **REFACTOR**: Improve code while keeping tests passing

### Code Quality

- Type annotations throughout
- Comprehensive docstrings
- Logging for observability
- Error handling at all levels

## Deployment

```bash
# Package Lambda
cd backend/lambda/event_processor
zip -r function.zip handler.py *.py

# Deploy via AWS CLI
aws lambda update-function-code \
  --function-name event-processor \
  --zip-file fileb://function.zip

# Or use AWS CDK/SAM for infrastructure as code
```

## Monitoring

### CloudWatch Metrics

- Processing time per batch
- Success/failure counts
- Parse errors
- Validation errors
- Enrichment errors
- Aggregation errors
- Archive errors

### CloudWatch Logs

All processing stages log to CloudWatch with structured logging:
- Request ID tracking
- Processing metrics
- Error details with stack traces

## Future Enhancements

- Parallel processing for large batches
- Async DynamoDB batch writes
- Enhanced caching for experiment/assignment data
- Compression algorithm selection
- Custom partitioning strategies
- Dead letter queue retry logic

## License

Proprietary - Part of Experimently platform

## Authors

Built with TDD methodology following EP-010 specification.
