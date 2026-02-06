# Test Plan Documentation

This directory contains detailed analysis and documentation for test plan CSV files used in the WebPDTool system.

## Documents

| Document | Description |
|----------|-------------|
| [XCU_ControlBoard_CANLIN_Analysis.md](XCU_ControlBoard_CANLIN_Analysis.md) | Complete analysis of the Magpie XCU Control Board CAN/LIN test plan |
| [Database_Model_Mapping_Verification.md](Database_Model_Mapping_Verification.md) | Verification of backend models against test plan CSV structure (includes identified gaps) |

## Test Plan File Structure

All test plan CSVs follow the PDTool4 format with these key sections:

1. **Column Definitions** - Field types, usage, and constraints
2. **Limit Types** - Validation rules (equality, partial, both, etc.)
3. **ExecuteName Types** - Measurement classes (PowerSet, CommandTest, etc.)
4. **Test Flow** - Phase-by-phase execution logic
5. **Code Mapping** - CSV fields to backend implementation

## Common Test Plan Patterns

### Power Initialization Pattern
```
PowerSet → Wait → DUT Ready
```

### Communication Test Pattern
```
SOC (Send Command) → Wait → Verify (Check Response)
```

### LIN Test Pattern (with Relay)
```
Close Relay → SOC → Verify → Open Relay
```

## Importing Test Plans

To import a CSV test plan into the database:

```bash
cd backend
python scripts/import_testplan.py \
  --project "PROJECT_CODE" \
  --station "STATION_CODE" \
  --csv-file "/path/to/testplan.csv"
```

## Related Code

- `backend/app/utils/csv_parser.py` - CSV parsing logic
- `backend/app/measurements/` - Measurement implementations
- `backend/app/models/test_plan.py` - Database models
- `backend/scripts/import_testplan.py` - Import script
