use std::collections::HashMap;

use rsheet_lib::cell_value::CellValue;
use rsheet_lib::cells;
use rsheet_lib::command_runner::CellArgument;

use crate::Coordinate;

pub fn str_to_coord(cell_str: &str) -> Result<Coordinate, String> {
    let digit_index = match cell_str.chars().position(|c| c.is_ascii_digit()) {
        Some(index) => index,
        None => return Err(format!("Cell parsing error: {}", cell_str)),
    };

    let (alpha, digit) = cell_str.split_at(digit_index);

    if alpha.is_empty() {
        return Err(format!("Cell parsing error: {}", cell_str));
    }
    let column = cells::column_name_to_number(alpha);
    let row = match digit.parse::<u32>() {
        Ok(row) => row,
        Err(_) => return Err(format!("Cell parsing error: {}", cell_str)),
    };

    Ok(Coordinate { x: column, y: row })
}

pub fn coord_to_str(coord: &Coordinate) -> String {
    let x_str = cells::column_number_to_name(coord.x);
    let y_str = coord.y.to_string();
    format!("{}{}", x_str, y_str)
}

pub fn check_cell_argument_error(cell_argument: &HashMap<String, CellArgument>) -> bool {
    for ca in cell_argument.values() {
        match ca {
            CellArgument::Matrix(mat) => {
                for m in mat {
                    for v in m {
                        if let CellValue::Error(_) = v {
                            return true;
                        }
                    }
                }
            }
            CellArgument::Vector(vec) => {
                for v in vec {
                    if let CellValue::Error(_) = v {
                        return true;
                    }
                }
            }
            CellArgument::Value(c) => {
                if let CellValue::Error(_) = c {
                    return true;
                }
            }
        }
    }

    false
}

pub fn matrix_contains_cell(matrix_str: &str, cell_str: &str) -> bool {
    let cell = match str_to_coord(cell_str) {
        Ok(c) => c,
        Err(_) => return false,
    };

    if !matrix_str.contains('_') {
        let matrix = match str_to_coord(matrix_str) {
            Ok(c) => c,
            Err(_) => return false,
        };
        return matrix == cell;
    }

    let mut matrixes = matrix_str.split('_');
    let start = match matrixes.next() {
        Some(s) => s,
        None => return false,
    };
    let end = match matrixes.next() {
        Some(s) => s,
        None => return false,
    };

    let start_c = match str_to_coord(start) {
        Ok(c) => c,
        Err(_) => return false,
    };
    let end_c = match str_to_coord(end) {
        Ok(c) => c,
        Err(_) => return false,
    };

    cell.x >= start_c.x && cell.x <= end_c.x && cell.y >= start_c.y && cell.y <= end_c.y
}
