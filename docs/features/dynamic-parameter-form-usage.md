# Dynamic Parameter Form Usage Guide

## Overview

The dynamic parameter form system provides an intelligent UI for inputting test parameters based on the selected test type and instrument mode. This eliminates manual JSON editing and reduces configuration errors.

## User Guide

### Creating a New Test Item with Parameters

1. **Open Test Plan Management**
   - Navigate to "測試計劃管理" page
   - Select a Project and Station from the filters

2. **Click "新增項目" (Add Item)**
   - Edit dialog opens

3. **Fill Basic Information**
   - 測試計劃名稱 (Test Plan Name): Optional group name
   - 測試項目名稱 (Item Name): Required test name
   - 項目鍵值 (Item Key): Optional unique key

4. **Select Test Type and Instrument Mode**
   - **測試類型 (Test Type)**: Select from dropdown (PowerRead, PowerSet, CommandTest, etc.)
   - **儀器模式 (Instrument Mode)**: Select from dropdown (appears after test type selection)
     - For PowerRead: DAQ973A, 34970A, KEITHLEY2015
     - For PowerSet: DAQ973A, MODEL2303, MODEL2306
     - For CommandTest: comport, tcpip

5. **Fill Test Parameters** (動態參數表單)
   - Form automatically displays required and optional parameters
   - Required parameters marked with * and "必填" label
   - Input controls adapt to parameter types:
     - **Number inputs**: Channel, Volt, Curr, Timeout (with appropriate precision)
     - **Dropdown selects**: Baud, Type, Item
     - **Text inputs**: Command, Port, Host (default)
   - Example values shown as placeholders
   - Real-time validation displays errors

6. **Set Limits and Other Fields**
   - 下限值 (Lower Limit): Minimum acceptable value
   - 上限值 (Upper Limit): Maximum acceptable value
   - 單位 (Unit): Measurement unit
   - 序號 (Sequence Order): Execution order

7. **Save**
   - Click "儲存" button
   - System validates all parameters
   - If validation fails, error messages appear
   - On success, test item is created with parameters stored in JSON format

### Editing Existing Test Items

1. **Click "編輯" (Edit)** on a test item row

2. **Modify Fields**
   - Existing parameters automatically populate the dynamic form
   - Change test type/instrument mode to reconfigure parameters
   - Update parameter values as needed

3. **Save Changes**
   - Click "儲存" to update

## Parameter Examples

### PowerRead - DAQ973A

**Required Parameters:**
- Instrument: `daq973a_1` (instrument ID)
- Channel: `101` (measurement channel number)
- Item: `volt` (measurement type: volt, curr, res, temp)
- Type: `DC` (measurement mode: DC or AC)

**Optional Parameters:**
- Range: Measurement range
- NPLC: Integration time (Number of Power Line Cycles)

### PowerSet - MODEL2306

**Required Parameters:**
- Instrument: `model2306_1`
- Channel: `1` (output channel)
- SetVolt: `5.0` (voltage to set in volts)
- SetCurr: `2.0` (current limit in amps)

**Optional Parameters:**
- OVP: Over-voltage protection threshold
- OCP: Over-current protection threshold
- Delay: Settling delay in milliseconds

### CommandTest - comport

**Required Parameters:**
- Port: `COM4` (serial port name)
- Baud: `9600` (baud rate)
- Command: `AT+VERSION` (command to send)

**Optional Parameters:**
- keyWord: `VERSION` (expected response keyword)
- spiltCount: `1` (response split count)
- splitLength: `10` (split length)
- EqLimit: Expected exact response

## Validation Rules

### Required Parameter Validation
- All required parameters must be filled
- Empty values (null, "", undefined) are rejected
- Error messages display missing parameters

### Parameter Type Validation
- Number inputs validate numeric format
- Select dropdowns ensure valid options
- Backend validates against MEASUREMENT_TEMPLATES

### Real-time Feedback
- ✓ Green checkmark: All validations pass
- ⚠️ Yellow alert: Missing or invalid parameters with suggestions
- Form submission blocked until validation passes

## Backward Compatibility

### Existing Test Items
- Test items without `switch_mode` or `parameters` remain functional
- Can be edited and saved normally
- Legacy fields (command, timeout, etc.) coexist with parameters
- No data migration required

### Migration Path
- Gradually convert legacy test items by editing them
- Fill in test type and instrument mode
- System automatically generates parameter structure
- Old CSV fields can be mapped to parameters

## Technical Details

### Data Storage
- Parameters stored in `test_plans.parameters` JSON column
- switch_mode stored in `test_plans.switch_mode` VARCHAR(50) column
- JSON format enables flexible parameter structures

### API Integration
- `GET /api/measurements/templates` - Fetch all templates
- `GET /api/measurements/templates/{test_type}` - Fetch specific type
- `POST /api/measurements/validate-params` - Validate parameters

### Frontend Architecture
- **DynamicParamForm.vue**: Reusable parameter form component
- **useMeasurementParams**: Composable for parameter logic
- **api/measurements.js**: API client for template operations

## Troubleshooting

### "請先選擇測試類型和儀器模式"
- **Cause**: No test type or instrument mode selected
- **Solution**: Select both test type and instrument mode from dropdowns

### "參數驗證錯誤"
- **Cause**: Missing required parameters
- **Solution**: Fill all required parameters (marked with *)
- Check error list for specific missing parameters

### Parameters Not Showing
- **Cause**: Test type not in MEASUREMENT_TEMPLATES
- **Solution**: Verify test type is supported
- Check available types in dropdown

### Cannot Save Test Item
- **Cause**: Form validation failing
- **Solution**:
  1. Check required fields (item_name, test_type, sequence_order)
  2. Verify parameter validation passes
  3. Review error messages in dialog

## Best Practices

1. **Always Select Instrument Mode**
   - Required for parameter validation
   - Ensures correct parameter structure

2. **Use Example Values as Reference**
   - Placeholder text shows expected format
   - Copy example structure for similar configurations

3. **Validate Before Saving**
   - Check for validation errors
   - Ensure all required parameters filled

4. **Consistent Naming**
   - Use consistent instrument IDs across test plans
   - Follow existing naming conventions

5. **Test Configuration**
   - Create a test item with minimal parameters first
   - Verify it works before adding optional parameters

## Future Enhancements (Phase 2)

- CSV upload with parameter preview and editing
- Batch parameter validation for imported items
- Parameter templates for quick configuration
- Instrument auto-discovery and selection
- Custom parameter definitions for new test types

## Related Documentation

- [TestPlan Parameters Architecture](./testplan-parameters-architecture.md)
- [Dynamic Parameter Form Design](../plans/2026-02-09-dynamic-parameter-form-design.md)
- [Measurement Implementation Guide](./measurement-implementations.md)
