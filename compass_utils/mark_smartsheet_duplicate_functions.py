

# Helper function to find cell in a row
def get_cell_by_column_name(row, column_name):
    column_id = column_map[column_name]
    return row.get_column(column_id)

# Return a new Row with updated cell values, else None to leave unchanged
def evaluate_row_and_build_updates(source_row):
    request_cell = get_cell_by_column_name(source_row, "Request ID")
    request_value = request_cell.display_value
    if request_value in update_list:
        
    # Build new cell value
        new_cell = smartsheet_client.models.Cell()
        new_cell.column_id = column_map["Forecast Stage"]
        new_cell.value = '7 - Duplicate Request'

    # Build the row to update
        new_row = smartsheet_client.models.Row()
        new_row.id = source_row.id
        new_row.cells.append(new_cell)

        return new_row
    
    return None